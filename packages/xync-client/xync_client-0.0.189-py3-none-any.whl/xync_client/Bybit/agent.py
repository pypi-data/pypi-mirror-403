import asyncio
import json
import logging
from asyncio import sleep, gather
from asyncio.tasks import create_task
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from hashlib import sha256
from http.client import HTTPException
from typing import Literal
from uuid import uuid4

import pyotp
import websockets
from aiohttp.http_exceptions import HttpProcessingError
from bybit_p2p import P2P
from bybit_p2p._exceptions import FailedRequestError
from payeer_api import PayeerAPI
from tortoise.timezone import now
from tortoise.transactions import in_transaction
from websockets import ConnectionClosedError
from x_client import df_hdrs
from x_model import init_db
from xync_bot import XyncBot

from xync_client.Abc.Ex import clean
from xync_client.Bybit.ex import ExClient
from xync_schema import models
from xync_schema.enums import OrderStatus, AgentStatus

from xync_schema.models import Agent

from xync_client.Abc.Agent import BaseAgentClient
from xync_client.Abc.xtype import FlatDict, BaseOrderReq, AdUpdReq, GetAdsReq
from xync_client.Bybit.etype.ad import AdPostRequest, AdRequest, Ad, AdStatusReq, MyAd
from xync_client.Bybit.etype.cred import CredEpyd, PaymentTerm, CredEx
from xync_client.Bybit.etype.order import (
    OrderRequest,
    PreOrderResp,
    OrderResp,
    CancelOrderReq,
    OrderItem,
    OrderFull,
    MsgFromApi,
    Status,
    OrderSellRequest,
    TakeAdReq,
    StatusChange,
    CountDown,
    ReceiveMsgFromWs,
    Read,
    SellerCancelChange,
    TopicWs,
)
from xync_client.Pms.Payeer.agent import PmAgentClient
from xync_client.loader import TORM, PAY_TOKEN, PRX


class NoMakerException(Exception):
    pass


class ShareException(Exception):
    pass


class AgentClient(BaseAgentClient):  # Bybit client
    headers = df_hdrs | {"accept-language": "ru-RU"}
    sec_hdrs: dict[str, str]
    # rewrite token for public methods
    api: P2P
    orders: dict[int, tuple[models.Order, OrderFull]] = {}  # pending
    cdx_cls: type[CredEx] = CredEx

    def __init__(
        self,
        agent: Agent,
        ex_client: ExClient,
        pm_clients: dict[int, PmAgentClient] = None,
        **kwargs,
    ):
        super().__init__(agent, ex_client, pm_clients, **kwargs)
        self.sec_hdrs = {
            "accept-language": "ru,en;q=0.9",
            "gdfp": agent.auth["Risktoken"],
            "tx-id": agent.auth["Risktoken"],
        }
        self.api = agent.auth.get("key") and P2P(
            testnet=False,
            api_key=agent.auth["key"],
            api_secret=agent.auth["sec"],  # , proxies=kwargs.get("proxies")
        )
        self.hist: dict | None = None
        self.completed_orders: list[int] | None = None

    """ Private METHs"""

    async def fiat_new(self, payment_type: int, real_name: str, account_number: str) -> FlatDict | None:
        method1 = await self._post(
            "/x-api/fiat/otc/user/payment/new_create",
            {"paymentType": payment_type, "realName": real_name, "accountNo": account_number, "securityRiskToken": ""},
        )
        if srt := method1["result"]["securityRiskToken"]:
            await self._check_2fa(srt)
            method2 = await self._post(
                "/x-api/fiat/otc/user/payment/new_create",
                {
                    "paymentType": payment_type,
                    "realName": real_name,
                    "accountNo": account_number,
                    "securityRiskToken": srt,
                },
            )
            return method2
        else:
            return logging.exception(method1)

    def get_payment_method(self, fiat_id: int) -> CredEpyd:
        return self.creds()[fiat_id]

    async def _get_creds(self) -> list[PaymentTerm]:
        data = self.api.get_user_payment_types()
        if data["ret_code"] > 0:
            return data
        return [PaymentTerm.model_validate(credex) for credex in data["result"] if credex["id"] != "-1"]

    async def _ott(self):
        t = await self._post("/x-api/user/private/ott")
        return t

    # 27
    async def fiat_upd(self, fiat_id: int, detail: str, name: str = None) -> dict:
        fiat = self.get_payment_method(fiat_id)
        fiat.realName = name
        fiat.accountNo = detail
        result = await self._post("/x-api/fiat/otc/user/payment/new_update", fiat.model_dump(exclude_none=True))
        srt = result["result"]["securityRiskToken"]
        await self._check_2fa(srt)
        fiat.securityRiskToken = srt
        result2 = await self._post("/fiat/otc/user/payment/new_update", fiat.model_dump(exclude_none=True))
        return result2

    # 28
    async def fiat_del(self, fiat_id: int) -> dict | str:
        data = {"id": fiat_id, "securityRiskToken": ""}
        method = await self._post("/x-api/fiat/otc/user/payment/new_delete", data)
        srt = method["result"]["securityRiskToken"]
        await self._check_2fa(srt)
        data["securityRiskToken"] = srt
        delete = await self._post("/x-api/fiat/otc/user/payment/new_delete", data)
        return delete

    async def switch_ads(self, new_status: AdStatusReq) -> dict:
        data = {"workStatus": new_status.name}  # todo: переделать на апи, там status 0 -> 1
        res = await self._post("/x-api/fiat/otc/maker/work-config/switch", data)
        return res

    @staticmethod
    def get_rate(list_ads: list) -> float:
        ads = [ad for ad in list_ads if set(ad["payments"]) - {"5", "51"}]
        return float(ads[0]["price"])

    async def get_my_ads(self, active: bool = True, page: int = 1) -> list[MyAd]:
        resp = self.api.get_ads_list(
            size="30", page=str(page), status=AdStatusReq.active if active else AdStatusReq.sold_out
        )
        ads = [MyAd.model_validate(ad) for ad in resp["result"]["items"]]
        # todo: вернуть, что бы спарсил все объявы, а не только первые 30
        # if resp["result"]["count"] > 30 * page:
        #     ads.extend(await self.get_my_ads(active, page + 1))
        return ads

    async def ads_share(self, cur_id: int = None) -> int:
        mq = models.MyAd.hot_mads_query([4]).filter(ad__maker=self.actor)
        if cur_id:
            mq = mq.filter(ad__pair_side__pair__cur_id=cur_id)
        mads: list[models.MyAd] = await mq.all()
        return len([await self.ad_share(mad.id) for mad in mads])

    async def ad_share(self, maid: int):
        myad = await models.MyAd.get(id=maid).prefetch_related(
            "ad__pair_side__pair__coin", "ad__pair_side__pair__cur", "ad__maker"
        )
        if myad.hex and myad.shared_at + timedelta(minutes=55) > now():  # if ad shared 55min ago or later
            return myad.get_url()
            # # check validity
            # data = await self._post("/x-api/fiat/otc/item/shareItem/info", {"shareCode": myad.hex.hex()})
            # logging.info("Waiting 3 seconds after fetch..")
            # await sleep(3)
            # if data["ret_code"] == 0:
            #     logging.info(f"{myad.ad.exid} successfully fetched")
            #     return myad.get_url()
            # else:
            #     return logging.error(f"{myad.ad.exid} fresh but not fetched! {data["ret_code"]}:{data["ret_msg"]}")
        data = await self._post("/x-api/fiat/otc/item/share", {"itemId": str(myad.ad.exid)})
        logging.info("Waiting 2 seconds after share..")
        await sleep(2)
        logging.debug(f"{myad.ad.exid} shared")
        if data["ret_code"] == 912300058:
            raise ShareException(f"Ad {myad.id}:{myad.ad.id}:{myad.ad.exid} agent:{myad.ad.maker_id} offline")
        elif data["ret_code"] == 912300059:
            raise ShareException(f"Торговля мейкера {myad.ad.maker_id} выключена")
        elif data["ret_code"] == 10006:
            logging.warning(f"Agent:{myad.ad.maker_id} слишком часто шейрит (ad:{myad.ad.exid}), ждем 5 сек..")
            await sleep(5)
            return await self.ads_share(maid)
        elif data["ret_code"] == 10007:
            raise ShareException(f"Авторизация агента {myad.ad.maker_id} слетела")
        elif data["ret_code"] == 912300064:
            raise ShareException(f"Ad {myad.ad.exid} maker:{myad.ad.maker_id} shared too much")
        elif data["ret_code"] != 0:  # Новая ошибка
            raise ShareException(data)
        url = data["result"]["shareLink"]
        resp = await self.session.get(url)
        side = "buy" if myad.ad.pair_side.is_sell else "sell"  # inverse for taker
        coin, cur = myad.ad.pair_side.pair.coin.ticker, myad.ad.pair_side.pair.cur.ticker
        pref = models.MyAd.WEB.format(side=side, coin=coin, cur=cur)
        hx = resp.url.query["by_web_link"].replace(pref, "")
        _r = await models.MyAd.filter(id=maid).update(hex=bytes.fromhex(hx), shared_at=now())
        await myad.refresh_from_db()
        return myad.get_url()

    def get_security_token_create(self):
        data = self._post("/x-api/fiat/otc/item/create", self.create_ad_body)
        if data["ret_code"] == 912120019:  # Current user can not to create add as maker
            raise NoMakerException(data)
        security_risk_token = data["result"]["securityRiskToken"]
        return security_risk_token

    async def _check_2fa(self, risk_token) -> int:
        data = {"risk_token": risk_token}
        res = await self._post("/x-api/user/public/risk/components", data, hdrs=self.sec_hdrs)
        if res["ret_msg"] != "success":
            raise HTTPException("get")
        cres = sorted(res["result"]["component_list"], key=lambda c: c["component_id"], reverse=True)
        vdata = {
            "risk_token": risk_token,
            "component_list": {c["component_id"]: await self.__get_2fa(c["component_id"], risk_token) for c in cres},
        }
        res = await self._post("/x-api/user/public/risk/verify", vdata, hdrs=self.sec_hdrs)
        if er_code := res["ret_code"] or res["result"]["ret_code"]:  # если код не 0, значит ошибка
            logging.error("Wrong 2fa, wait 5 secs and retry..")
            await sleep(5)
            return await self._check_2fa(risk_token)
        return er_code

    async def __get_2fa(
        self, typ: Literal["google2fa", "email_verify", "payment_password_verify", "phone_verify"], rt: str = None
    ):
        res = {"ret_msg": "success"}
        if typ != "google2fa":
            data = {"risk_token": rt, "component_id": typ}
            res = await self._post("/x-api/user/public/risk/send/code", data, hdrs=self.sec_hdrs)
        if res["ret_msg"] == "success":
            if typ == "google2fa":
                bybit_secret = self.agent.auth["2fa"]
                totp = pyotp.TOTP(bybit_secret)
                return totp.now()
            elif typ == "email_verify":
                return self.gmail.bybit_code()
            elif typ == "payment_password_verify":
                hp = sha256(self.agent.auth["pass"].encode()).hexdigest()
                return hp
        elif cool_down := int(res["result"]["cool_down"]):
            await sleep(cool_down)
            return self.__get_2fa(typ, rt)
        raise Exception("2fa fail")

    async def get_ad(self, ad_exid: int) -> Ad:
        return Ad(**self.api.get_ad_details(itemId=ad_exid)["result"])

    def _post_ad(self, risk_token: str):
        self.create_ad_body.update({"securityRiskToken": risk_token})
        data = self._post("/x-api/fiat/otc/item/create", self.create_ad_body)
        return data

    # создание объявлений
    def post_create_ad(self, token: str):
        result__check_2fa = self._check_2fa(token)
        assert result__check_2fa["ret_msg"] == "success", "2FA code wrong"

        result_add_ad = self._post_ad(token)
        if result_add_ad["ret_msg"] != "SUCCESS":
            print("Wrong 2fa on Ad creating, wait 9 secs and retry..")
            sleep(9)
            return self._post_create_ad(token)
        self.last_ad_id.append(result_add_ad["result"]["itemId"])

    def ad_new(self, ad: AdPostRequest):
        data = self.api.post_new_ad(**ad.model_dump())
        return data["result"]["itemId"] if data["ret_code"] == 0 else data

    async def _ad_upd(self, req: AdUpdReq):
        upd = AdRequest({})
        params = upd.model_dump()
        data = self.api.update_ad(**params)
        return data["result"] if data["ret_code"] == 0 else data

    def get_security_token_update(self) -> str:
        self.update_ad_body["id"] = self.last_ad_id
        data = self._post("/x-api/fiat/otc/item/update", self.update_ad_body)
        security_risk_token = data["result"]["securityRiskToken"]
        return security_risk_token

    def post_update_ad(self, token):
        result__check_2fa = self._check_2fa(token)
        assert result__check_2fa["ret_msg"] == "success", "2FA code wrong"

        result_update_ad = self.update_ad(token)
        if result_update_ad["ret_msg"] != "SUCCESS":
            print("Wrong 2fa on Ad updating, wait 10 secs and retry..")
            sleep(10)
            return self._post_update_ad(token)
        # assert result_update_ad['ret_msg'] == 'SUCCESS', "Ad isn't updated"

    def update_ad(self, risk_token: str):
        self.update_ad_body.update({"securityRiskToken": risk_token})
        data = self._post("/x-api/fiat/otc/item/update", self.update_ad_body)
        return data

    def ad_del(self, ad_id: int):
        data = self.api.remove_ad(itemId=ad_id)
        return data

    async def __preorder_request(self, ad_id: int) -> PreOrderResp:
        res = await self._post("/x-api/fiat/otc/item/simple", json={"item_id": str(ad_id)})
        if res["ret_code"] == 0:
            res = res["result"]
        return PreOrderResp.model_validate(res)

    async def _order_request(self, bor: BaseOrderReq, bbot: XyncBot) -> OrderResp:
        por: PreOrderResp = await self.__preorder_request(bor.ad_id)
        req = OrderRequest(
            itemId=por.id,
            tokenId=bor.coin_exid,
            currencyId=bor.cur_exid,
            side="1" if bor.is_sell else "0",
            amount=f"{bor.amount:.2f}".rstrip("0").rstrip("."),
            curPrice=por.curPrice,
            quantity=str(round(bor.amount / float(por.price), bor.coin_scale)),
            flag="amount",
            # online="0"
        )
        if bor.is_sell:
            credex = await models.CredEx.get(
                cred__person_id=self.actor.person_id,
                cred__pmcur__pm__pmexs__exid=[pp for pp in por.payments if pp == bor.pmex_exid][0],  # bor.pmex_exid
                cred__pmcur__pm__pmexs__ex_id=self.ex_client.ex.id,
                cred__pmcur__cur__ticker=bor.cur_exid,
            )
            req = OrderSellRequest(**req.model_dump(), paymentType=bor.pmex_exid, paymentId=str(credex.exid))
        # вот непосредственно сам запрос на ордер
        return await self.__order_create(req, bor, bbot)

    async def __order_create(self, req: OrderRequest | OrderSellRequest, bor: BaseOrderReq, bbot: XyncBot) -> OrderResp:
        hdrs = {"Risktoken": self.sec_hdrs["gdfp"]}
        res: dict = await self._post("/x-api/fiat/otc/order/create", json=req.model_dump(), hdrs=hdrs)
        if res["ret_code"] == 0:
            resp = OrderResp.model_validate(res["result"])
        elif res["ret_code"] == 10001:
            logging.error(req.model_dump(), "POST", self.session._base_url)
            raise HTTPException()
        elif res["ret_code"] == 912120030 or res["ret_msg"] == "The price has changed, please try again later.":
            resp = await self._order_request(bor, bbot)
        else:
            logging.exception(res)
        if not resp.orderId and resp.needSecurityRisk:
            if rc := await self._check_2fa(resp.securityRiskToken):
                await bbot.send(self.actor.person.user.username_id, f"Bybit 2fa: {rc}")
                raise Exception(f"Bybit 2fa: {rc}")
            # еще раз уже с токеном
            req.securityRiskToken = resp.securityRiskToken
            resp = await self.__order_create(req, bor, bbot)
        return resp

    async def cancel_order(self, order_id: str) -> bool:
        cr = CancelOrderReq(orderId=order_id)
        res = await self._post("/x-api/fiat/otc/order/cancel", cr.model_dump())
        return res["ret_code"] == 0

    async def get_order_info(self, order_id: str) -> OrderFull:
        data = await self._post("/x-api/fiat/otc/order/info", json={"orderId": order_id})
        return OrderFull.model_validate(data["result"])

    def get_chat_msg(self, order_id):
        data = self._post("/x-api/fiat/otc/order/message/listpage", json={"orderId": order_id, "size": 100})
        msgs = [
            {"text": msg["message"], "type": msg["contentType"], "role": msg["roleType"], "user_id": msg["userId"]}
            for msg in data["result"]["result"]
            if msg["roleType"] not in ("sys", "alarm")
        ]
        return msgs

    def block_user(self, user_id: str):
        return self._post("/x-api/fiat/p2p/user/add_block_user", {"blockedUserId": user_id})

    def unblock_user(self, user_id: str):
        return self._post("/x-api/fiat/p2p/user/delete_block_user", {"blockedUserId": user_id})

    def user_review_post(self, order_id: str):
        return self._post(
            "/x-api/fiat/otc/order/appraise/modify",
            {
                "orderId": order_id,
                "anonymous": "0",
                "appraiseType": "1",  # тип оценки 1 - хорошо, 0 - плохо. При 0 - обязательно указывать appraiseContent
                "appraiseContent": "",
                "operateType": "ADD",  # при повторном отправлять не 'ADD' -> а 'EDIT'
            },
        )

    def my_reviews(self):
        return self._post(
            "/x-api/fiat/otc/order/appraiseList",
            {"makerUserId": self.actor.exid, "page": "1", "size": "10", "appraiseType": "1"},  # "0" - bad
        )

    async def get_pending_orders(
        self, side: int = None, status: int = None, begin_time: int = None, end_time: int = None, token_id: str = None
    ):
        res = await self._post(
            "/x-api/fiat/otc/order/pending/simplifyList",
            {
                "status": status,
                "tokenId": token_id,
                "beginTime": begin_time,
                "endTime": end_time,
                "side": side,  # 1 - продажа, 0 - покупка
                "page": 1,
                "size": 20,
            },
        )
        if res["ret_code"] == 0:
            return {int(o["id"]): OrderItem(**o) for o in res["result"]["items"]}
        return res["ret_code"]

    def get_orders_done(self, begin_time: int, end_time: int, status: int, side: int, token_id: str):
        return self._post(
            "/x-api/fiat/otc/order/simplifyList",
            {
                "status": status,  # 50 - завершено
                "tokenId": token_id,
                "beginTime": begin_time,
                "endTime": end_time,
                "side": side,  # 1 - продажа, 0 - покупка
                "page": 1,
                "size": 10,
            },
        )

    async def get_api_orders(
        self,
        page: int = 1,
        begin_time: int = None,
        end_time: int = None,
        status: int = None,
        side: int = None,
        token_id: str = None,
    ):
        try:
            lst = self.api.get_orders(
                page=page,
                # status=status,  # 50 - завершено
                # tokenId=token_id,
                # beginTime=begin_time,
                # endTime=end_time,
                # side=side, # 1 - продажа, 0 - покупка
                size=30,
            )
        except FailedRequestError as e:
            if e.status_code == 10000:
                await sleep(9)
                await self.get_api_orders(page, begin_time, end_time)  # , status, side, token_id)
        ords = {int(o["id"]): OrderItem.model_validate(o) for o in lst["result"]["items"]}
        for oid, o in ords.items():
            if o.status != Status.completed.value or oid in self.completed_orders:
                continue
            order = await self.get_order_full(o.id)
            order_db = await self.order_save(order)
            await sleep(1)
            dmsgs = self.api.get_chat_messages(orderId=oid, size=200)["result"]["result"][::-1]
            msgs = [MsgFromApi.model_validate(m) for m in dmsgs if m["msgType"] in (1, 2, 7, 8)]
            if order_db.ad.auto_msg:
                msgs and msgs.pop(0)
            msgs_db = [
                models.Msg(
                    order=order_db,
                    read=m.isRead,
                    to_maker=m.userId != order.makerUserId,
                    **({"txt": m.message} if m.msgType == 1 else {"file": await self.ex_client.file_upsert(m.message)}),
                    sent_at=int(m.createDate[:-3]),
                )
                for m in msgs
            ]
            _ = await models.Msg.bulk_create(msgs_db, ignore_conflicts=True)
        logging.info(f"orders page#{page} imported ok!")
        if len(ords) == 30:
            await self.get_api_orders(page + 1, begin_time, end_time, status, side, token_id)

    # async def order_stat(self, papi: PayeerAPI):
    #     for t in papi.history():
    #         os = self.api.get_orders(page=1, size=30)

    # @staticmethod
    # def premium_up(mad: Ad, cad: Ad, k: Literal[-1, 1]):
    #     mpc, mpm, cpc, cpm = Decimal(mad.price), Decimal(mad.premium), Decimal(cad.price), Decimal(cad.premium)
    #     new_premium = cpm - k * step(mad, cad, 2)
    #     if Decimal(mad.premium) == new_premium:  # Если нужный % и так уже стоит
    #         raise ValueError("wrong premium", mad, cad)
    #     if round(cpc * new_premium / cpm, 2) == m
    #     mad.premium = new_premium.to_eng_string()

    async def take_ad(self, req: TakeAdReq, bbot: XyncBot):
        if req.price and req.is_sell and req.cur_:
            ...  # todo call the get_ad_details() only if lack of data
        # res = self.api.get_ad_details(itemId=req.ad_id)["result"]
        # ad: Ad = Ad.model_validate(res)
        # pmexs = await models.PmEx.filter(ex_id=self.actor.ex_id, pm_id=req.pm_id)
        # if len(pmexs) > 1:
        #     pmexs = [p for p in pmexs if p.exid in ad.payments]
        #
        # # todo: map pm->cred_pattern
        # pmexid = exids.pop() if (exids := set(ad.payments) & set(px.exid for px in pmexs)) else "40"
        pmexid = str(req.pm_id)
        coinex = await models.CoinEx.get(coin_id=req.coin_id, ex=self.ex_client.ex)
        curex = await models.CurEx.get(cur_id=req.cur_id, ex=self.ex_client.ex)

        # if ad.side: # продажа, я (тейкер) покупатель
        #     pmexs = await models.PmEx.filter(ex_id=self.actor.ex_id, pm_id=req.pm_id)
        #     if len(pmexs) > 1:
        #         pmexs = [p for p in pmexs if p.name.endswith(f" ({ad.currencyId})")]
        # else:
        #     pmexs = await models.CredEx.filter(
        #         ex_id=self.actor.ex_id, cred__person_id=self.actor.person_id,
        #         cred__pmcur__pm_id=req.pm_id, cred__pmcur__cur__ticker=ad.currencyId
        #    )
        # req.pm_id = pmexs[0].exid
        # req.quantity = round(req.amount / float(ad.price) - 0.00005, 4)  # todo: to get the scale from coinEx

        bor = BaseOrderReq(
            ad_id=str(req.ad_id),
            amount=req.amount,
            is_sell=req.is_sell,
            cur_exid=curex.exid,
            coin_exid=coinex.exid,
            coin_scale=coinex.scale,
            pmex_exid=pmexid,
        )
        resp: OrderResp = await self._order_request(bor, bbot)
        return resp

    async def watch_payeer(self, mcs: dict[int, "AgentClient"], bbot: XyncBot):
        await models.CoinEx.get(coin_id=1, ex=self.actor.ex).prefetch_related("coin")
        await models.CurEx.get(cur_id=1, ex=self.actor.ex).prefetch_related("cur")
        post_pmexs = set(await models.PmEx.filter(pm_id=366, ex=self.actor.ex).prefetch_related("pm"))
        i = 0
        while True:
            try:
                breq = GetAdsReq(coin_id=1, cur_id=1, is_sell=False, limit=50)
                bs = await self.ex_client.ads(breq, post_pmexs=post_pmexs)
                bs = [b for b in bs if float(b.price) < 100 or int(b.userId) in mcs.keys()]
                if bs:
                    ad: Ad = bs[0]
                    await bbot.send(
                        193017646,
                        f"price: {ad.price}\nnick: {ad.nickName}\nprice: {ad.price}"
                        f"\nqty: {ad.quantity} [{ad.minAmount}-{ad.maxAmount}]",
                    )
                    am = min(float(ad.maxAmount), max(8000 + i, float(ad.minAmount)))
                    req = TakeAdReq(
                        ad_id=ad.id,
                        amount=am,
                        pm_id=14,
                        is_sell=False,
                        coin_id=1,
                        cur_id=1,
                    )
                    ord_resp: OrderResp = await self.take_ad(req, bbot)
                    # order: OrderFull = OrderFull(**self.api.get_order_details(orderId=ord_resp.orderId)["result"])
                    order: OrderFull = await self.get_order_info(ord_resp.orderId)
                    odb = await self.order_save(order)
                    t = await models.Transfer(order=odb, amount=odb.amount, updated_at=now())
                    await t.fetch_related("order__cred__pmcur__cur")
                    # res = await self.pm_clients[366].send(t)
                    await sleep(2)
                    self.api.mark_as_paid(
                        orderId=str(odb.exid),
                        paymentType=str(order.paymentTermList[0].paymentType),  # pmex.exid
                        paymentId=order.paymentTermList[0].id,  # credex.exid
                    )
                    await sleep(3)
                    if int(ad.userId) in mcs:
                        mcs[int(ad.userId)].api.release_assets(orderId=order.id)

                await sleep(5)

                sreq = GetAdsReq(coin_id=1, cur_id=1, is_sell=True, limit=50, kwargs={"post_pmexs": post_pmexs})
                ss = await self.ex_client.ads(sreq, post_pmexs=post_pmexs)
                ss = [s for s in ss if float(s.price) > 92 or int(s.userId) in mcs.keys()]
                if ss:
                    ad: Ad = ss[0]
                    await bbot.send(
                        193017646,
                        f"price: {ad.price}\nnick: {ad.nickName}\nprice: {ad.price}"
                        f"\nqty: {ad.quantity} [{ad.minAmount}-{ad.maxAmount}]",
                    )
                    am = min(float(ad.maxAmount), max(10000 + i, float(ad.minAmount)))
                    req = TakeAdReq(
                        ad_id=ad.id,
                        amount=am,
                        pm_id=14,
                        is_sell=True,
                        coin_id=1,
                        cur_id=1,
                    )
                    ord_resp: OrderResp = await self.take_ad(req, bbot)
                    # order: OrderFull = OrderFull(**self.api.get_order_details(orderId=ord_resp.orderId)["result"])
                    order: OrderFull = await self.get_order_info(ord_resp.orderId)
                    odb = await self.order_save(order)
                    # t = await models.Transfer(order=odb, amount=odb.amount, updated_at=now())
                    # await t.fetch_related("order__cred__pmcur__cur")
                    # res = await self.pm_clients[366].check_in(t)
                    await sleep(2)
                    if int(ad.userId) in mcs:
                        mcs[int(ad.userId)].api.mark_as_paid(
                            orderId=str(odb.exid),
                            paymentType=str(order.paymentTermList[0].paymentType),  # pmex.exid
                            paymentId=order.paymentTermList[0].id,  # credex.exid
                        )
                    await sleep(3)
                    self.api.release_assets(orderId=order.id)
                await sleep(5)

            except Exception as e:
                logging.exception(e)
                await sleep(30)
            except HttpProcessingError as e:
                logging.error(e)
            print(end=".", flush=True)
            i += 1
            await sleep(5)

    async def boost_acc(self):
        await sleep(45)
        for i in range(10):
            am = 500 + i
            req = TakeAdReq(ad_id="1856989782009487360", amount=am, pm_id=366)
            ord_resp: OrderResp = await self.take_ad(req)
            order: OrderFull = await self.get_order_full(int(ord_resp.orderId))
            odb = await self.order_save(order)
            t = await models.Transfer(order=odb, amount=odb.amount, updated_at=now())
            await t.fetch_related("order__cred__pmcur__cur")
            await self.pm_clients[366].send(t)
        ...

    async def load_pending_orders(self):
        po: dict[int, OrderItem] = await self.get_pending_orders()
        if isinstance(po, int):  # если код ошибки вместо результата
            raise ValueError(po)
        self.orders = {
            o.exid: (o, await self.get_order_full(o.exid)) for o in await models.Order.filter(exid__in=po.keys())
        }
        for oid in po.keys() - self.orders.keys():
            await self.load_order(oid)

    async def _start_listen(self):
        t = await self._ott()
        ts = int(float(t["time_now"]) * 1000)
        did = self.agent.auth["cookies"]["deviceId"]
        u = f"wss://ws2.bybit.com/private?appid=bybit&os=web&deviceid={did}&timestamp={ts}"
        async with websockets.connect(u) as websocket:
            auth_msg = json.dumps({"req_id": did, "op": "login", "args": [t["result"]]})
            await websocket.send(auth_msg)

            sub_msg = json.dumps({"op": "subscribe", "args": ["FIAT_OTC_TOPIC", "FIAT_OTC_ONLINE_TOPIC"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"SUPER_DEAL"}']})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"OTC_ORDER_STATUS"}']})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"WEB_THREE_SELL"}']})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"APPEALED_CHANGE"}']})
            await websocket.send(sub_msg)

            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.cashier.order"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.cashier.order-eftd-complete-privilege-event"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.cashier.order-savings-product-event"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.deal-core.order-savings-complete-event"]})
            await websocket.send(sub_msg)

            sub_msg = json.dumps({"op": "subscribe", "args": ["FIAT_OTC_TOPIC", "FIAT_OTC_ONLINE_TOPIC"]})
            await websocket.send(sub_msg)
            try:
                while resp := await websocket.recv():
                    if data := json.loads(resp):
                        logging.info(
                            f" {now().strftime('%H:%M:%S')} upd: {data.get('topic')}:{data.get('type')}:{data.get('status')}"
                        )
                        await self.proc(data)
            except ConnectionClosedError as e:
                logging.warning(e)
                await self._start_listen()

    async def proc(self, data: dict):
        if topic := data.get("topic"):
            if topic == TopicWs.OTC_ORDER_STATUS.name:
                if (typ := data["type"]) == "STATUS_CHANGE":
                    upd = StatusChange.model_validate(data["data"])
                    if not upd.status:
                        logging.error(data["data"])
                    order_db, order = await self.load_order(upd.exid)
                    if upd.status == OrderStatus.created:
                        logging.info(f"Order {upd.exid} CREATED at {upd.created_at}")
                        # await self.got_new_order(order_db, order)

                        # # сразу уменьшаем доступный остаток монеты/валюты
                        # await self.money_upd(order_db)
                        # if upd.side:  # я покупатель - ждем мою оплату
                        #     _dest = order.paymentTermList[0].accountNo
                        #     if not re.match(r"^([PpРр])\d{7,10}\b", _dest):
                        #         return
                        #     await order_db.fetch_related("ad__pair_side__pair", "cred__pmcur__cur")
                        #     await self.send_payment(order_db)
                        # case OrderStatus.created:
                        if upd.ad__pair_side__is_sell == 0:  # я продавец, ждем когда покупатель оплатит
                            # check_payment() # again
                            ...
                            # if not (pmacdx := await self.get_pma_by_cdex(order)):
                            #     return
                            # pma, cdx = pmacdx
                            # am, tid = await pma.check_in(
                            #     float(order.amount),
                            #     cdx.cred.pmcur.cur.ticker,
                            #     # todo: почему в московском час.поясе?
                            #     datetime.fromtimestamp(float(order.transferDate) / 1000),
                            # )
                            # if not tid:
                            #     logging.info(f"Order {order.id} created at {order.createDate}, not paid yet")
                            #     return
                            # try:
                            #     t, is_new = await models.Transfer.update_or_create(
                            #         dict(
                            #             amount=int(float(order.amount) * 100),
                            #             order=order_db,
                            #         ),
                            #         pmid=tid,
                            #     )
                            # except IntegrityError as e:
                            #     logging.error(tid)
                            #     logging.error(order)
                            #     logging.exception(e)
                            #
                            # if not is_new:  # если по этому платежу уже отпущен другая продажа
                            #     return
                            #
                            # # если висят незавершенные продажи с такой же суммой
                            # pos = (await self.get_orders_active(1))["result"]
                            # pos = [
                            #     o
                            #     for o in pos.get("items", [])
                            #     if (
                            #         o["amount"] == order.amount
                            #         and o["id"] != upd.exid
                            #         and int(order.createDate) < int(o["createDate"]) + 15 * 60 * 1000
                            #         # get full_order from o, and cred or pm from full_order:
                            #         and self.api.get_order_details(orderId=o["id"])["result"][
                            #             "paymentTermList"
                            #         ][0]["accountNo"]
                            #         == order.paymentTermList[0].accountNo
                            #     )
                            # ]
                            # curex = await models.CurEx.get(cur__ticker=order.currencyId, ex=self.ex_client.ex)
                            # pos_db = await models.Order.filter(
                            #     exid__not=order.id,
                            #     cred_id=order_db.cred_id,
                            #     amount=int(float(order.amount) * 10**curex.scale),
                            #     status__not_in=[OrderStatus.completed, OrderStatus.canceled],
                            #     created_at__gt=now() - timedelta(minutes=15),
                            # )
                            # if pos or pos_db:
                            #     await self.ex_client.bot.send(
                            #         f"[Duplicate amount!]"
                            #         f"(https://www.bybit.com/ru-RU/p2p/orderList/{order.id})",
                            #         self.actor.person.user.username_id,
                            #     )
                            #     logging.warning("Duplicate amount!")
                            #     return
                            #
                            # # !!! ОТПРАВЛЯЕМ ДЕНЬГИ !!!
                            # self.api.release_assets(orderId=upd.exid)
                            # logging.info(
                            #     f"Order {order.id} created, paid before #{tid}:{am} at {order.createDate}, and RELEASED at {now()}"
                            # )
                        elif upd.ad__pair_side__is_sell == 1:  # я покупатель - ждем мою оплату
                            # pay()
                            logging.warning(f"Order {upd.exid} CREATED2 at {now()}")

                    if upd.status == OrderStatus.paid:
                        if order_db.status == OrderStatus.paid:
                            return
                        await order_db.update_from_dict(
                            {
                                "status": OrderStatus.paid,
                            }
                        ).save()
                        logging.info(f"Order {order.exid} payed at {order_db.updated_at}")

                    elif upd.status == OrderStatus.appealed_by_seller:  # just any appealed
                        # todo: appealed by WHO? щас наугад стоит by_seller
                        await order_db.update_from_dict(
                            {
                                "status": OrderStatus.appealed_by_seller,
                            }
                        ).save()
                        logging.info(f"Order {order.exid} appealed at {order_db.updated_at}")

                    elif upd.status == OrderStatus.canceled:
                        await order_db.update_from_dict({"status": OrderStatus.canceled}).save()
                        logging.info(f"Order {order.exid} canceled at {datetime.now()}")
                        # await self.money_upd(order_db)

                    elif upd.status == OrderStatus.completed:
                        await order_db.refresh_from_db()
                        if order_db.status != OrderStatus.completed:
                            await order_db.update_from_dict(
                                {
                                    "status": OrderStatus.completed,
                                }
                            ).save(update_fields=["status"])
                        # await self.money_upd(order_db)
                    elif upd.status == OrderStatus.appeal_disputed:
                        logging.info(f"Order {order.exid} appeal_disputed at {datetime.now()}")
                    else:
                        logging.warning(f"Order {order.exid} {upd.status.name} {datetime.now()}")
                elif typ == "COUNT_DOWN":
                    upd = CountDown.model_validate(data["data"])
                else:
                    logging.warning(data, f"Order UNKNOWN TYPE {typ}")

            elif topic == TopicWs.OTC_USER_CHAT_MSG_V2.name:
                if (typ := data["type"]) == "RECEIVE":
                    upd = ReceiveMsgFromWs.model_validate(data["data"])
                    if upd.roleType == "user":
                        order_db, order = await self.load_order(upd.orderId)
                        # await order_db.got_msg(upd)
                        if not isinstance(order_db.ad, models.Ad) or not isinstance(order_db.ad.cond, models.Cond):
                            await order_db.fetch_related("ad__cond")
                        if order_db.ad.cond.raw_txt != clean(upd.message):
                            msg, _ = await models.Msg.update_or_create(
                                {
                                    "to_maker": (upd.userId == self.actor.exid) != order_db.ami_maker(self.actor.id),
                                    "sent_at": upd.createDate,
                                },
                                txt=upd.message,
                                order=order_db,
                            )
                            if not upd.message:
                                ...
                            # if im_buyer and (g := re.match(r"^[PpРр]\d{7,10}\b", upd.message)):
                            #     if not order_db.cred.detail.startswith(dest := g.group()):
                            #         order_db.cred.detail = dest
                            #         await order_db.save()
                            #     await self.send_payment(order_db)
                elif typ == "READ":
                    # msg_read()
                    upd = Read.model_validate(data["data"])

            elif (
                topic == TopicWs.SELLER_CANCEL_CHANGE.name
            ):  # я покупатель, уже проставил оплату, продавец запросил отмену
                upd = SellerCancelChange.model_validate(data["data"])
                order_db, order = await self.load_order(upd.id)
                await order_db.cancel_request()

        else:  # topic is None
            if not data.get("success"):
                raise HTTPException(401 if data["ret_msg"] == "Request not authorized" else data)
            else:
                return  # success login, subscribes, input

    async def _get_order_full(self, order_exid: int) -> OrderFull:
        order_dict: dict = self.api.get_order_details(orderId=order_exid)["result"]
        return OrderFull.model_validate(order_dict)

    async def money_upd(self, odb: models.Order):
        # обновляем остаток монеты
        await odb.fetch_related("ad__pair_side__pair", "ad__my_ad__credexs__cred__fiat", "cred__pmcur", "transfer")
        ass = await models.Asset.get(addr__coin_id=odb.ad.pair_side.pair.coin_id, addr__actor=self.actor)
        # обновляем остаток валюты
        im_maker = odb.ad.maker_id == self.actor.id
        im_seller = odb.ad.pair_side.is_sell == im_maker
        if im_maker:
            if _fiats := [cx.cred.fiat for cx in odb.ad.my_ad.credexs if cx.cred.fiat]:
                fiat = _fiats[0]
                await fiat.fetch_related("cred__pmcur__pm")
            else:
                raise ValueError(odb, "No Fiat")
        elif im_seller:  # im taker
            fltr = dict(cred__person_id=self.actor.person_id)
            fltr |= (
                {"cred__ovr_pm_id": odb.cred.ovr_pm_id, "cred__pmcur__cur_id": odb.cred.pmcur.cur_id}
                if odb.cred.ovr_pm_id
                else {"cred__pmcur_id": odb.cred.pmcur_id}
            )
            if not (fiat := await models.Fiat.get_or_none(**fltr).prefetch_related("cred__pmcur__pm")):
                raise ValueError(odb, "No Fiat")
        fee = round(odb.amount * (fiat.cred.pmcur.pm.fee or 0) * 0.0001)
        # k = int(im_seller) * 2 - 1  # im_seller: 1, im_buyer: -1
        if odb.status == OrderStatus.created:
            if im_seller:
                ass.free -= odb.quantity
                ass.freeze += odb.quantity
            else:  # я покупатель
                fiat.amount -= odb.amount + fee
        elif odb.status == OrderStatus.completed:
            if im_seller:
                fiat.amount += odb.amount
            else:  # я покупатель
                ass.free += odb.quantity
        elif odb.status == OrderStatus.canceled:
            if im_seller:
                ass.free += odb.quantity
                ass.freeze -= odb.quantity
            else:  # я покупатель
                fiat.amount += odb.amount + fee
        else:
            logging.exception(odb.id, f"STATUS: {odb.status.name}")
        await ass.save(update_fields=["free", "freeze"])
        await fiat.save(update_fields=["amount"])
        logging.info(f"Order #{odb.id} {odb.status.name}. Fiat: {fiat.amount}, Asset: {ass.free}")

    async def send_payment(self, order_db: models.Order):
        if order_db.status != OrderStatus.created:
            return
        fmt_am = round(order_db.amount * 10**-2, 2)
        pma, cur = await self.get_pma_by_pmex(order_db)
        async with in_transaction():
            # отмечаем ордер на бирже "оплачен"
            pmex = await models.PmEx.get(pm_id=order_db.cred.pmcur.pm_id, ex=self.actor.ex)
            credex = await models.CredEx.get(cred=order_db.cred, ex=self.actor.ex)
            self.api.mark_as_paid(
                orderId=str(order_db.exid),
                paymentType=pmex.exid,  # pmex.exid
                paymentId=str(credex.exid),  # credex.exid
            )
            # проверяем не отправляли ли мы уже перевод по этому ордеру
            if t := await models.Transfer.get_or_none(order=order_db, amount=order_db.amount):
                await pma.bot.send(
                    f"Order# {order_db.exid}: Double send {fmt_am}{cur} to {order_db.cred.detail} #{t.pmid}!",
                    self.actor.person.user.username_id,
                )
                raise Exception(
                    f"Order# {order_db.exid}: Double send {fmt_am}{cur} to {order_db.cred.detail} #{t.pmid}!"
                )

            # ставим в бд статус "оплачен"
            order_db.status = OrderStatus.paid
            await order_db.save()
            # создаем перевод в бд
            t = models.Transfer(order=order_db, amount=order_db.amount, updated_at=now())
            # отправляем деньги
            tid, img = await pma.send(t)
            t.pmid = tid
            await t.save()
            await self.send_receipt(str(order_db.exid), tid)  # отправляем продавцу чек
            logging.info(f"Order {order_db.exid} PAID at {datetime.now()}: {fmt_am}!")

    async def send_receipt(self, oexid: str, tid: int) -> tuple[PmAgentClient | None, models.CredEx] | None:
        try:
            if res := self.api.upload_chat_file(upload_file=f"tmp/{tid}.png").get("result"):
                await sleep(0.5)
                self.api.send_chat_message(orderId=oexid, contentType="pic", message=res["url"], msgUuid=uuid4().hex)
        except Exception as e:
            logging.error(e)
        await sleep(0.5)
        self.api.send_chat_message(orderId=oexid, contentType="str", message=f"#{tid}", msgUuid=uuid4().hex)

    async def get_pma_by_cdex(self, order: OrderFull) -> tuple[PmAgentClient | None, models.CredEx] | None:
        cdxs = await models.CredEx.filter(
            ex=self.ex_client.ex,
            exid__in=[ptl.id for ptl in order.paymentTermList],
            cred__person=self.actor.person,
        ).prefetch_related("cred__pmcur__cur")
        pmas = [pma for cdx in cdxs if (pma := self.pm_clients.get(cdx.cred.pmcur.pm_id))]
        if not len(pmas):
            # raise ValueError(order.paymentTermList, f"No pm_agents for {order.paymentTermList[0].paymentType}")
            return None
        elif len(pmas) > 1:
            logging.error(order.paymentTermList, f">1 pm_agents for {cdxs[0].cred.pmcur.pm_id}")
        else:
            return pmas[0], cdxs[0]

    async def get_pma_by_pmex(self, order_db: models.Order) -> tuple[PmAgentClient, str]:
        pma = self.pm_clients.get(order_db.cred.pmcur.pm_id)
        if pma:
            return pma, order_db.cred.pmcur.cur.ticker
        logging.error(f"No pm_agents for {order_db.cred.pmcur.pm_id}")


def ms2utc(msk_ts_str: str):
    return datetime.fromtimestamp(int(msk_ts_str) / 1000, timezone(timedelta(hours=3), name="MSK"))


def detailed_diff(str1, str2):
    matcher = SequenceMatcher(None, str1, str2)
    result = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            result.append(str1[i1:i2])
        elif tag == "delete":
            result.append(f"[-{str1[i1:i2]}]")
        elif tag == "insert":
            result.append(f"[+{str2[j1:j2]}]")
        elif tag == "replace":
            result.append(f"[{str1[i1:i2]}→{str2[j1:j2]}]")

    return "".join(result)


# @post_save(models.Race)
# async def race_upserted(
#     _cls: type[models.Race], race: models.Race, created: bool, _db: BaseDBAsyncClient, _updated: list[str]
# ):
#     logging.warning(f"Race {race.id} is now upserted")
#     asyncio.all_tasks()
#     if created:
#         ...
#     else:  # параметры гонки изменены
#         ...


async def main():
    logging.basicConfig(level=logging.INFO)
    cn = await init_db(TORM)

    agent = (
        await models.Agent.filter(actor__ex_id=4, auth__isnull=False, status__gt=AgentStatus.off, id=2)
        .prefetch_related(
            "actor__ex",
            "actor__person__user__gmail",
            "actor__my_ads__my_ad__race",
            "actor__my_ads__pair_side__pair__cur",
            "actor__my_ads__pms",
        )
        .first()
    )
    # b.add_handler(MessageHandler(cond_start_handler, command("cond")))
    ex = await models.Ex.get(name="Bybit")
    prx = PRX and "http://" + PRX
    ecl: ExClient = ex.client(proxy=prx)
    abot = XyncBot(PAY_TOKEN, cn)
    # pmas = await models.PmAgent.filter(active=True, user_id=1).prefetch_related("pm", "user__gmail")
    # pm_clients = {pma.pm_id: pma.client(abot) for pma in pmas}
    cl: AgentClient = agent.client(ecl, proxy=prx)

    # req = TakeAdReq(ad_id=1955696985964089344, amount=504, pm_id=128)
    # await cl.take_ad(req)

    # await cl.actual_cond()
    # cl.get_api_orders(),  # 10, 1738357200000, 1742504399999

    # await cl.ex_client.set_coins()
    # await cl.ex_client.set_curs()
    # await cl.ex_client.set_pairs()
    # await cl.ex_client.set_pms()

    # await cl.load_creds()
    # await cl.load_my_ads()

    my_ad = await models.MyAd[5]
    await cl.ad_share(my_ad.id)

    ms = await models.Agent.filter(
        actor__ex_id=4, auth__isnull=False, status__gt=AgentStatus.off, actor__person__user__id__in=[3]
    ).prefetch_related(
        "actor__ex",
        "actor__person__user__gmail",
        "actor__my_ads__my_ad__race",
        "actor__my_ads__pair_side__pair__cur",
        "actor__my_ads__pms",
    )
    mcs = {m.actor.exid: m.client(ecl) for m in ms}

    await gather(
        # create_task(cl.start()),
        create_task(cl.watch_payeer(mcs, abot)),
    )
    # ensure_future(cl.start(True))
    # await cl.boost_acc()

    # создание гонок по мои активным объявам:
    # for ma in cl.my_ads():
    #     my_ad = await models.MyAd.get(ad__exid=ma.id).prefetch_related('ad__pms', 'ad__pair_side__pair')
    #     race, _ = await models.Race.update_or_create(
    #         {"started": True, "vm_filter": True, "target_place": 5},
    #         road=my_ad
    #     )

    # for name in names:
    #     s, _ = await models.Synonym.update_or_create(typ=SynonymType.name, txt=name)
    #     await s.curs.add(rub.cur)

    pauth = (await models.PmAgent[1]).auth
    papi = PayeerAPI(pauth["email"], pauth["api_id"], pauth["api_sec"])
    hist: dict = papi.history(count=1000)
    hist |= papi.history(count=1000, append=list(hist.keys())[-1])
    hist |= papi.history(count=1000, append=list(hist.keys())[-1])
    cl.hist = hist

    # cl.completed_orders = await models.Order.filter(status=OrderStatus.completed, transfer__isnull=False).values_list(
    #     "exid", flat=True
    # )
    # await cl.get_api_orders()  # 43, 1741294800000, 1749157199999)

    # await cl.cancel_order(res.orderId)
    await cl.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down")
