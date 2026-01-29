import logging
import re
from abc import abstractmethod
from asyncio import sleep
from collections import defaultdict
from difflib import SequenceMatcher

from aiohttp import ClientSession, ClientResponse
from msgspec import Struct
from pydantic import BaseModel
from pyro_client.client.file import FileClient
from tortoise.exceptions import MultipleObjectsReturned, IntegrityError, OperationalError
from x_client.aiohttp import Client as HttpClient
from xync_client.Bybit.etype.ad import AdsReq
from xync_schema import models
from xync_schema.enums import FileType
from xync_schema import xtype

from xync_client.Abc.AdLoader import AdLoader
from xync_client.Abc.xtype import PmEx, MapOfIdsList, GetAdsReq, BaseActor, BaseAd, BaseCounteragent
from xync_client.pm_unifier import PmUnifier, PmUni


class BaseExClient(HttpClient, AdLoader):
    host: str = None
    cur_map: dict[int, str] = {}
    unifier_class: type = PmUnifier
    logo_pre_url: str
    ex: models.Ex

    coin_x2e: dict[int, tuple[str, int]] = {}
    coin_e2x: dict[str, int] = {}
    cur_x2e: dict[int, tuple[str, int, int]] = {}
    cur_e2x: dict[str, int] = {}
    pm_x2e: dict[int, str | int] = {}
    pm_e2x: dict[str | int, int] = {}
    pairs_e2x: dict[int, dict[int, tuple[int, int]]] = defaultdict(defaultdict)
    pairs_x2e: dict[int, tuple[int, int, int]] = defaultdict(defaultdict)
    actor_x2e: dict[int, int] = {}
    actor_e2x: dict[int, models.Actor] = {}
    ad_x2e: dict[int, int] = {}
    ad_e2x: dict[int, models.Ad] = {}

    def __init__(
        self,
        ex: models.Ex,
        attr: str = "host_p2p",
        headers: dict[str, str] = None,
        cookies: dict[str, str] = None,
        proxy: models.Proxy = None,
    ):
        self.ex = ex
        super().__init__(self.host or getattr(ex, attr), headers, cookies, proxy and str(proxy))

    @abstractmethod
    def pm_type_map(self, typ: models.PmEx) -> str: ...

    # 19: Список поддерживаемых валют тейкера
    @abstractmethod
    async def curs(self) -> dict[str, xtype.CurEx]:  # {cur.ticker: cur}
        ...

    # 20: Список платежных методов
    @abstractmethod
    async def pms(self, cur: models.Cur = None) -> dict[int | str, PmEx]:  # {pm.exid: pm}
        ...

    # 21: Список платежных методов по каждой валюте
    @abstractmethod
    async def cur_pms_map(self) -> MapOfIdsList:  # {cur.exid: [pm.exid]}
        ...

    # 22: Список торгуемых монет (с ограничением по валютам, если есть)
    @abstractmethod
    async def coins(self) -> dict[str, xtype.CoinEx]:  # {coin.ticker: coin}
        ...

    # 23: Список пар валюта/монет
    @abstractmethod
    async def pairs(self) -> tuple[MapOfIdsList, MapOfIdsList]: ...

    # converters
    async def x2e_coin(self, coin_id: int) -> tuple[str, int]:  # coinex.exid
        if not self.coin_x2e.get(coin_id):
            exid, scale = await models.CoinEx.get(coin_id=coin_id, ex=self.ex).values_list("exid", "scale")
            self.coin_x2e[coin_id] = exid, scale
            self.coin_e2x[exid] = coin_id
        return self.coin_x2e[coin_id]

    async def e2x_coin(self, exid: str) -> int:  # coin.id
        if not self.coin_e2x.get(exid):
            coin_id, scale = await models.CoinEx.get(exid=exid, ex=self.ex).values_list("coin_id", "scale")
            self.coin_x2e[coin_id] = exid, scale
            self.coin_e2x[exid] = coin_id
        return self.coin_e2x[exid]

    async def x2e_cur(self, cur_id: int) -> tuple[str, int, int]:  # curex.exid
        if not self.cur_x2e.get(cur_id):
            exid, scale, mnm = await models.CurEx.get(cur_id=cur_id, ex=self.ex).values_list("exid", "scale", "minimum")
            self.cur_x2e[cur_id] = exid, scale, mnm
            self.cur_e2x[exid] = cur_id
        return self.cur_x2e[cur_id]

    async def e2x_cur(self, exid: str) -> int:  # cur.id
        if not self.cur_e2x.get(exid):
            cur_id, scale, mnm = await models.CurEx.get(exid=exid, ex=self.ex).values_list("cur_id", "scale", "minimum")
            self.cur_e2x[exid] = cur_id
            self.cur_x2e[cur_id] = exid, scale, mnm
        return self.cur_e2x[exid]

    async def x2e_pm(self, pm_id: int) -> str:  # pmex.exid
        if not self.pm_x2e.get(pm_id):
            self.pm_x2e[pm_id] = (await models.PmEx.get(pm_id=pm_id, ex=self.ex)).exid
            self.pm_e2x[self.pm_x2e[pm_id]] = pm_id
        return self.pm_x2e[pm_id]

    async def e2x_pm(self, exid: str | int) -> int:  # pm.id
        if not self.pm_e2x.get(exid):
            self.pm_e2x[exid] = (await models.PmEx.get(exid=exid, ex=self.ex)).pm_id
            self.pm_x2e[self.pm_e2x[exid]] = exid
        return self.pm_e2x[exid]

    # pair_side
    async def ccs2pair(self, coin_id: int, cur_id: int, is_sell: bool) -> int:  # ex cur+coin+is_sale -> x pair.id
        if not self.pairs_e2x.get(coin_id, {}).get(cur_id):
            self.pairs_e2x[coin_id][cur_id] = (
                await models.PairSide.filter(pair__coin_id=coin_id, pair__cur_id=coin_id)
                .order_by("is_sell")
                .values_list("id", flat=True)
            )
        return self.pairs_e2x[coin_id][cur_id][int(is_sell)]

    async def pair2ccs(self, xid: int) -> tuple[int, int, int]:  # coinex.exid
        if not self.pairs_x2e.get(xid):
            ps = await models.PairSide.get(id=xid).prefetch_related("pair")
            self.pairs_x2e[xid] = ps.pair.coin_id, ps.pair.cur_id, ps.is_sell
        return self.pairs_x2e[xid]

    async def e2x_pair(self, coin_exid: str, cur_exid: str, is_sell: bool) -> int:  # ex cur+coin+is_sale -> x pair.id
        coin_id = await self.e2x_coin(coin_exid)
        cur_id = await self.e2x_cur(cur_exid)
        return await self.ccs2pair(coin_id, cur_id, is_sell)

    async def x2e_pair(self, pair_side_id: int) -> tuple[str, str, int]:  # coinex.exid
        coin_id, cur_id, is_sell = await self.pair2ccs(pair_side_id)
        coin_exid = await self.x2e_coin(coin_id)
        cur_exid = await self.x2e_cur(cur_id)
        return coin_exid[0], cur_exid[0], is_sell

    async def x2e_actor(self, actor_id: int) -> int:  # actor.exid
        if not self.actor_x2e.get(actor_id):
            actor = await models.Actor[actor_id]
            self.actor_x2e[actor_id] = actor.exid
            self.actor_e2x[self.actor_x2e[actor_id]] = actor
        return self.actor_x2e[actor_id]

    async def e2x_actor(self, base_actor: BaseActor) -> models.Actor:
        if not self.actor_e2x.get(base_actor.exid):
            actor = await self.actor_save(base_actor)
            self.actor_e2x[base_actor.exid] = actor
            self.actor_x2e[actor.id] = base_actor.exid
        return self.actor_e2x[base_actor.exid]

    async def x2e_ad(self, ad_id: int) -> int:  # ad.exid
        if not self.ad_x2e.get(ad_id):
            ad = await models.Ad[ad_id]
            self.ad_x2e[ad_id] = ad.exid
            self.ad_e2x[ad.exid] = ad
        return self.ad_x2e[ad_id]

    async def e2x_ad(self, ad_exid: int) -> models.Ad:
        if not self.ad_e2x.get(ad_exid):
            if not (ad := await models.Ad.get_or_none(exid=ad_exid, maker__ex=self.ex)):
                return None
            self.ad_e2x[ad_exid] = ad
            self.ad_x2e[ad.id] = ad_exid
        return self.ad_e2x[ad_exid]

    # 24: Список объяв по (buy/sell, cur, coin, pm)
    async def ads(self, xreq: GetAdsReq, **kwargs) -> list[xtype.BaseAd]:
        ereq = AdsReq(
            coin_id=(await self.x2e_coin(xreq.coin_id))[0],
            cur_id=(await self.x2e_cur(xreq.cur_id))[0],
            is_sell=str(int(xreq.is_sell)),
            pm_ids=[await self.x2e_pm(pid) for pid in xreq.pm_ids],
            # size=str(xreq.limit),
            # page=str(xreq.page),
        )
        if xreq.amount:
            ereq.amount = str(xreq.amount)
        return await self._ads(ereq, **kwargs)

    @abstractmethod
    async def _ads(self, ereq: BaseModel, **kwargs) -> list[BaseAd]: ...

    # 42: Чужая объява по id
    @abstractmethod
    async def ad(self, ad_id: int) -> xtype.BaseAd: ...

    # Преобразрование объекта объявления из формата биржи в формат xync
    @abstractmethod
    async def ad_epyd2pydin(self, ad: BaseAd) -> xtype.BaseAd: ...  # my_uid: for MyAd

    # 99: Страны
    async def countries(self) -> list[Struct]:
        return []

    # Импорт валют Cur-ов (с CurEx-ами)
    async def set_curs(self, cookies: dict = None) -> bool:
        # Curs
        cur_pyds: dict[str, xtype.CurEx] = await self.curs()
        old_curs = {c.ticker: c.id for c in await models.Cur.all()}
        curs: dict[int | str, models.Cur] = {
            exid: (
                await models.Cur.update_or_create(
                    {"rate": cur_pyd.rate or 0, "id": old_curs.get(cur_pyd.ticker, await models.Cur.all().count() + 1)},
                    ticker=cur_pyd.ticker,
                )
            )[0]
            for i, (exid, cur_pyd) in enumerate(cur_pyds.items())
        }
        curexs = [
            models.CurEx(**c.model_dump(exclude_none=True), cur=curs[c.exid], ex=self.ex) for c in cur_pyds.values()
        ]
        # CurEx
        await models.CurEx.bulk_create(curexs, update_fields=["minimum", "scale"], on_conflict=["cur_id", "ex_id"])

    # Импорт Pm-ов (с PmCur-, PmEx- и Pmcurex-ами) и валют (с CurEx-ами) с биржи в бд
    async def set_pms(self, bot: FileClient, cookies: dict = None) -> bool:
        if cookies:
            self.session.cookie_jar.update_cookies(cookies)
        curs: dict[int | str, models.Cur] = {
            exid: (await models.Cur.update_or_create({"rate": cur_pyd.rate or 0}, ticker=cur_pyd.ticker))[0]
            for exid, cur_pyd in (await self.curs()).items()
        }
        # Pms
        pmexs_epyds: dict[int | str, PmEx] = {
            k: v for k, v in sorted((await self.pms()).items(), key=lambda x: x[1].name) if v.name
        }  # sort by name
        pms: dict[int | str, models.Pm] = dict({})
        prev = 0, "", "", None  # id, normd-name, orig-name
        cntrs: list[tuple[str, str]] = [
            (n.lower(), s and s.lower()) for n, s in await models.Country.all().values_list("name", "short")
        ]
        common_reps = await models.PmRep.filter(ex_id__isnull=True)
        reps = self.ex.pm_reps.related_objects
        uni = self.unifier_class(cntrs, reps + common_reps)
        for k, pmex in pmexs_epyds.items():
            pmu: PmUni = uni(pmex.name)
            country_id = (
                await models.Country.get(name__iexact=cnt).values_list("id", flat=True)
                if (cnt := pmu.country)
                else None
            )
            if prev[2] == pmex.name and pmu.country == prev[3]:  # оригинальное имя не уникально на этой бирже
                logging.warning(f"Pm: '{pmex.name}' duplicated with ids {prev[0]}: {k} on {self.ex.name}")
                # новый Pm не добавляем, а берем старый с этим названием
                pm_ = pms.get(prev[0], await models.Pm.get_or_none(norm=prev[1], country_id=country_id))
                # и добавляем PmEx для него
                await models.PmEx.update_or_create({"name": pmex.name}, ex=self.ex, exid=k, pm=pm_)
            elif (
                prev[1] == pmu.norm and pmu.country == prev[3]
            ):  # 2 разных оригинальных имени на этой бирже совпали при нормализации
                logging.error(
                    f"Pm: {pmex.name}&{prev[2]} overnormd as {pmu.norm} with ids {prev[0]}: {k} on {self.ex.name}"
                )
                # новый Pm не добавляем, только PmEx для него
                # новый Pm не добавляем, а берем старый с этим названием
                pm_ = pms.get(prev[0], await models.Pm.get_or_none(norm=prev[1], country_id=country_id))
                # и добавляем.обновляем PmEx для него
                await models.PmEx.update_or_create({"pm": pm_}, ex=self.ex, exid=k, name=pmex.name)
            else:
                pmin = models.Pm.validate({**pmu.model_dump(), "country_id": country_id, "typ": pmex.typ})
                try:
                    pms[k], _ = await models.Pm.update_or_create(**pmin.df_unq())
                except (MultipleObjectsReturned, IntegrityError) as e:
                    raise e
            prev = k, pmu.norm, pmex.name, pmu.country
        await models.PmCur.update_or_create(  # todo: NA HU YA???
            cur=await models.Cur.get(ticker="THB"), pm=await models.Pm.get(norm="cash in person")
        )

        # Pmexs
        async with ClientSession(headers=getattr(self, "logo_headers", None)) as ss:
            pmexs = [
                models.PmEx(
                    # todo: refact logo
                    exid=k,
                    ex=self.ex,
                    pm=pm,
                    name=pmexs_epyds[k].name,
                    logo=await self.logo_save(pmexs_epyds[k].logo, bot, ss),
                )
                for k, pm in pms.items()
            ]

        await models.PmEx.bulk_create(pmexs, on_conflict=["ex_id", "exid"], update_fields=["pm_id", "logo_id", "name"])
        # PmEx banks
        for k, pmex in pmexs_epyds.items():
            if banks := pmex.banks:
                pmex = await models.PmEx.get(ex=self.ex, exid=k)  # pm=pms[k],
                for b in banks:
                    await models.PmExBank.update_or_create({"name": b.name}, exid=b.exid, pmex=pmex)

        cur2pms = await self.cur_pms_map()
        # # Link PayMethods with currencies
        pmcurs = set()
        for cur_id, exids in cur2pms.items():
            for exid in exids:
                if not (pm_id := pms.get(exid) and pms[exid].id):
                    if pmex := await models.PmEx.get_or_none(ex=self.ex, exid=exid):
                        pm_id = pmex.pm_id
                    else:
                        logging.critical(f"For cur {cur_id} not found pm#{exid}")
                        continue
                if cur_db := curs.get(cur_id):
                    pmcurs.add((await models.PmCur.update_or_create(cur=cur_db, pm_id=pm_id))[0])
        # pmcurexs = [Pmcurex(pmcur=pmcur, ex=self.ex) for pmcur in pmcurs]
        # await Pmcurex.bulk_create(pmcurexs)
        return True

    async def logo_save(self, url: str | None, bot: FileClient, ss: ClientSession) -> models.File | None:
        if url or (file := None):
            if not url.startswith("https:"):
                if not url.startswith("/"):
                    url = "/" + url
                url = "https://" + self.logo_pre_url + url
            return await self.file_upsert(url, bot, ss)
        return file

    # Импорт монет (с CoinEx-ами) с биржи в бд
    async def set_coins(self):
        coinexs: dict[str, xtype.CoinEx] = await self.coins()
        coins_db: dict[int, models.Coin] = {
            c.exid: (
                await models.Coin.update_or_create({"scale": c.scale or self.coin_scales[c.ticker]}, ticker=c.ticker)
            )[0]
            for c in coinexs.values()
        }
        coinexs_db: list[models.CoinEx] = [
            models.CoinEx(
                scale=(scl := c.scale or self.coin_scales[c.ticker]),
                coin=coins_db[c.exid],
                ex=self.ex,
                exid=c.exid,
                minimum=c.minimum and c.minimum * 10**scl,
            )
            for c in coinexs.values()
        ]
        await models.CoinEx.bulk_create(coinexs_db, update_fields=["minimum"], on_conflict=["coin_id", "ex_id"])
        return True

    # Импорт пар биржи в бд
    async def set_pairs(self):
        curs: dict[str, models.Cur] = {
            k: (await models.Cur.get_or_create(ticker=c.ticker))[0] for k, c in (await self.curs()).items()
        }
        coins: dict[str, xtype.CoinEx] = {
            k: (await models.Coin.get_or_create(ticker=c.ticker))[0] for k, c in (await self.coins()).items()
        }
        prs: tuple[dict, dict] = await self.pairs()
        for is_sell in (0, 1):
            for cur, coinz in prs[is_sell].items():
                for coin in coinz:
                    pair, _ = await models.Pair.get_or_create(coin=coins[coin], cur=curs[cur])
                    # pairex, _ = await models.PairEx.get_or_create(pair=pair, ex=self.ex)  # todo: разные ли комишки на покупку и продажу?
                    await models.PairSide.update_or_create(is_sell=is_sell, pair=pair)
        return True

    # Сохранение чужого объявления (с Pm-ами) в бд
    # async def ad_pydin2db(self, ad_pydin: BaseAdIn) -> models.Ad:
    #     dct = ad_pydin.model_dump()
    #     dct["exid"] = dct.pop("id")
    #     ad_in = models.Ad.validate(dct)
    #     ad_db, _ = await models.Ad.update_or_create(**ad_in.df_unq())
    #     await ad_db.credexs.add(*getattr(ad_pydin, "credexs_", []))
    #     await ad_db.pmexs.add(*getattr(ad_pydin, "pmexs_", []))
    #     return ad_db

    async def file_upsert(self, url: str, bot: FileClient, ss: ClientSession = None) -> models.File:
        if not (file := await models.File.get_or_none(name__startswith=url.split("?")[0])):
            ss = ss or self.session
            if (resp := await ss.get(url)).ok:
                byts = await resp.read()
                upf, ref = await bot.save_doc(byts, resp.content_type)
                await sleep(0.3)
                typ = FileType[resp.content_type.split("/")[-1]]
                file, _ = await models.File.update_or_create({"ref": ref, "size": len(byts), "typ": typ}, name=url)
                # fr = await pbot.get_file(file.ref)  # check
        return file

    async def _proc(self, resp: ClientResponse, bp: dict | str = None) -> dict | str:
        if resp.status in (403,):
            proxy = await models.Proxy.filter(valid=True, country__short__not="US").order_by("-updated_at").first()
            cookies = self.session.cookie_jar.filter_cookies(self.session._base_url)
            self.session = ClientSession(
                self.session._base_url,
                headers=self.session.headers,
                cookies=cookies or None,
                proxy=proxy and str(proxy),
            )
            return await self.METHS[resp.method](self, resp.url.path, bp)
        return await super()._proc(resp, bp)

    # ad cond loader
    all_conds: dict[int, tuple[str, set[int]]] = {}
    cond_sims: dict[int, int] = defaultdict(set)
    rcond_sims: dict[int, set[int]] = defaultdict(set)  # backward
    tree: dict = {}

    async def old_conds_load(self):
        # пока не порешали рейс-кондишн, очищаем сиротские условия при каждом запуске
        # [await c.delete() for c in await Cond.filter(ads__isnull=True)]
        self.all_conds = {
            c.id: (c.raw_txt, {a.maker.exid for a in c.ads})
            for c in await models.Cond.all().prefetch_related("ads__maker")
        }
        for curr, old in await models.CondSim.filter().values_list("cond_id", "cond_rel_id"):
            self.cond_sims[curr] = old
            self.rcond_sims[old] |= {curr}

        self.build_tree()
        a = set()

        def check_tree(tre):
            for p, c in tre.items():
                a.add(p)
                check_tree(c)

        for pr, ch in self.tree.items():
            check_tree(ch)
        if ct := set(self.tree.keys()) & a:
            logging.exception(f"cycle cids: {ct}")

    async def person_save(self, base_person: BaseActor) -> models.Person:
        if not (person := await models.Person.get_or_none(note=(note := f"{self.ex.id}:{base_person.exid}"))):
            name = base_person.name if isinstance(base_person, BaseCounteragent) else base_person.nick
            person = await models.Person.create(name=name, note=note)
        elif isinstance(base_person, BaseCounteragent) and not person.name:
            # если персона не новая, но имени не было, а щас передано - обновим
            person.name = base_person.name
            await person.save(update_fields=["name"])
        return person

    async def actor_save(self, base_actor: BaseActor) -> models.Actor:
        if not (actor := await models.Actor.get_or_none(exid=base_actor.exid, ex=self.ex)):
            # если это новый актор - делаем создание персоны со стороны биржи
            person = await self.person_save(base_actor)
            actor = await models.Actor.create(exid=base_actor.exid, name=base_actor.nick, person=person, ex=self.ex)
        return actor

    async def ad_save(self, base_ad: BaseAd) -> models.Ad:
        # if ad_db := await models.Ad.get_or_none(exid=base_ad.exid, maker__ex=self.ex):
        #     ...  # load new data
        #     return ad_db
        cond = await self.load_cond(base_ad.cond_txt, base_ad.maker_exid)
        _, cur_scale, _cur_min = await self.x2e_cur(await self.e2x_cur(base_ad.curex_exid))
        _, coin_scale = await self.x2e_coin(await self.e2x_coin(base_ad.coinex_exid))
        badd = base_ad.model_dump()
        badd.update(
            amount=int((base_ad.amount or base_ad.quantity * base_ad.price) * 10**cur_scale),
            max_fiat=int(base_ad.max_fiat * 10**cur_scale),
            min_fiat=int(base_ad.min_fiat * 10**cur_scale),
            premium=int(base_ad.premium * 100_00),
            price=int(base_ad.price * 10**cur_scale),
            quantity=int((base_ad.quantity or base_ad.amount / base_ad.price) * 10**coin_scale),
            maker_id=(await self.e2x_actor(base_ad.maker)).id,
            cond_id=cond and cond.id,
            pair_side_id=await self.e2x_pair(base_ad.coinex_exid, base_ad.curex_exid, bool(base_ad.side.value)),
            pms=await models.Pm.filter(pmexs__ex=self.ex, pmexs__exid__in=base_ad.pmex_exids),
        )
        ad = xtype.BaseAd.model_validate(badd)
        ad_upd = models.Ad.validate(ad.model_dump(), with_pk=False)
        try:
            ad_db, _ = await models.Ad.update_or_create(**ad_upd.df_unq())
        except OperationalError as e:
            raise e
        await ad_db.pms.clear()
        await ad_db.pms.add(*ad.pms)
        return ad_db

    async def load_cond(self, txt: str, maker_exid: int) -> models.Cond | None:
        # если текст пустой
        if not (cleaned := clean(txt)):
            return None
        # если точно такое условие уже есть в бд
        if cid := {oc[0]: ci for ci, oc in self.all_conds.items()}.get(cleaned):
            return await models.Cond[cid]
        # создаем новое условие
        return await self.cond_new(cleaned, {maker_exid})

    async def old_load_cond(self, ad: BaseAd) -> models.Ad:
        _sim, cid = None, None
        ad_db = await models.Ad.get_or_none(exid=ad.exid, maker__ex=self.ex).prefetch_related("cond")
        # если точно такое условие уже есть в бд
        if not (cleaned := clean(ad.cond_txt)) or (
            cid := {oc[0]: ci for ci, oc in self.all_conds.items()}.get(cleaned)
        ):
            # и объява с таким ид уже есть, но у нее другое условие
            if ad_db and ad_db.cond_id != cid:
                old_cid = ad_db.cond_id
                # то обновляем ид ее условия
                ad_db.cond_id = cid
                await ad_db.save(update_fields=["cond_id"])
                logging.info(f"{ad.maker_name} upd cond#{ad_db.cond_id}->{cid}")
                # если после переназначения объяве нового условия, со старым условием не осталось объяв, то удаляем его
                if not len((old_cond := await models.Cond.get(id=old_cid).prefetch_related("ads")).ads):
                    await old_cond.delete()
                    logging.warning(f"Cond#{old_cid} deleted!")
            return ad_db or await self.ad_save(ad)
        # если эта объява в таким ид уже есть в бд, но с другим условием (или без), а текущего условия еще нет в бд
        if ad_db:
            await ad_db.fetch_related("cond__ads", "maker")
            if not ad_db.cond_id or (
                # у измененного условия этой объявы есть другие объявы?
                (rest_ads := set(ad_db.cond.ads) - {ad_db})
                and
                # другие объявы этого условия принадлежат другим юзерам
                {ra.maker_id for ra in rest_ads} - {ad_db.maker_id}
            ):
                # создадим новое условие и присвоим его только текущей объяве
                cond = await self.cond_new(cleaned, {int(ad.maker_exid)})
                ad_db.cond_id = cond.id
                await ad_db.save(update_fields=["cond_id"])
                ad_db.cond = cond  # todo: а это зачем?
                return ad_db
            # а если других объяв со старым условием этой обявы нет, либо они все этого же юзера
            # обновляем условие (в тч во всех ЕГО объявах)
            ad_db.cond.last_ver = ad_db.cond.raw_txt
            ad_db.cond.raw_txt = cleaned
            try:
                await ad_db.cond.save()
            except IntegrityError as e:
                raise e
            await self.cond_upd(ad_db.cond, {ad_db.maker.exid})
            # и подправим коэфициенты похожести нового текста
            await self.fix_rel_sims(ad_db.cond_id, cleaned)
            return ad_db
        # нет ни объяв ни таких условий еще в бд, все новое
        cond = await self.cond_new(cleaned, {int(ad.maker_exid)})
        ad_db = await self.ad_save(ad, cond.id)
        ad_db.cond = cond
        return ad_db

    async def cond_new(self, txt: str, uids: set[int]) -> models.Cond:
        new_cond, _ = await models.Cond.update_or_create(raw_txt=txt)
        # и максимально похожую связь для нового условия (если есть >= 60%)
        await self.cond_upd(new_cond, uids)
        return new_cond

    async def cond_upd(self, cond: models.Cond, uids: set[int]):
        self.all_conds[cond.id] = cond.raw_txt, uids
        # и максимально похожую связь для нового условия (если есть >= 60%)
        old_cid, sim = await self.cond_get_max_sim(cond.id, cond.raw_txt, uids)
        await self.actual_sim(cond.id, old_cid, sim)

    def find_in_tree(self, cid: int, old_cid: int) -> bool:
        if p := self.cond_sims.get(old_cid):
            if p == cid:
                return True
            return self.find_in_tree(cid, p)
        return False

    async def cond_get_max_sim(self, cid: int, txt: str, uids: set[int]) -> tuple[int | None, int | None]:
        # находим все старые тексты похожие на 90% и более
        if len(txt) < 15:
            return None, None
        sims: dict[int, int] = {}
        for old_cid, (old_txt, old_uids) in self.all_conds.items():
            if len(old_txt) < 15 or uids == old_uids:
                continue
            elif not self.can_add_sim(cid, old_cid):
                continue
            if sim := get_sim(txt, old_txt):
                sims[old_cid] = sim
        # если есть, берем самый похожий из них
        if sims:
            old_cid, sim = max(sims.items(), key=lambda x: x[1])
            await sleep(0.3)
            return old_cid, sim
        return None, None

    def can_add_sim(self, cid: int, old_cid: int) -> bool:
        if cid == old_cid:
            return False
        elif self.cond_sims.get(cid) == old_cid:
            return False
        elif self.find_in_tree(cid, old_cid):
            return False
        elif self.cond_sims.get(old_cid) == cid:
            return False
        elif cid in self.rcond_sims.get(old_cid, {}):
            return False
        elif old_cid in self.rcond_sims.get(cid, {}):
            return False
        return True

    async def fix_rel_sims(self, cid: int, new_txt: str):
        for rel_sim in await models.CondSim.filter(cond_rel_id=cid).prefetch_related("cond"):
            if sim := get_sim(new_txt, rel_sim.cond.raw_txt):
                rel_sim.similarity = sim
                await rel_sim.save()
            else:
                await rel_sim.delete()

    async def actual_cond(self):
        for curr, old in await models.CondSim.all().values_list("cond_id", "cond_rel_id"):
            self.cond_sims[curr] = old
            self.rcond_sims[old] |= {curr}
        for cid, (txt, uids) in self.all_conds.items():
            old_cid, sim = await self.cond_get_max_sim(cid, txt, uids)
            await self.actual_sim(cid, old_cid, sim)
            # хз бля чо это ваще
            # for ad_db in await models.Ad.filter(direction__pairex__ex=self.ex).prefetch_related("cond", "maker"):
            #     ad = Ad(id=str(ad_db.exid), userId=str(ad_db.maker.exid), remark=ad_db.cond.raw_txt)
            #     await self.cond_upsert(ad, force=True)

    async def actual_sim(self, cid: int, old_cid: int, sim: int):
        if not sim:
            return
        if old_sim := await models.CondSim.get_or_none(cond_id=cid):
            if old_sim.cond_rel_id != old_cid:
                if sim > old_sim.similarity:
                    logging.warning(f"R {cid}: {old_sim.similarity}->{sim} ({old_sim.cond_rel_id}->{old_cid})")
                    await old_sim.update_from_dict({"similarity": sim, "old_rel_id": old_cid}).save()
                    self._cond_sim_upd(cid, old_cid)
            elif sim != old_sim.similarity:
                logging.info(f"{cid}: {old_sim.similarity}->{sim}")
                await old_sim.update_from_dict({"similarity": sim}).save()
        else:
            await models.CondSim.create(cond_id=cid, cond_rel_id=old_cid, similarity=sim)
            self._cond_sim_upd(cid, old_cid)

    def _cond_sim_upd(self, cid: int, old_cid: int):
        if old_old_cid := self.cond_sims.get(cid):  # если старый cid уже был в дереве:
            self.rcond_sims[old_old_cid].remove(cid)  # удаляем из обратного
        self.cond_sims[cid] = old_cid  # а в прямом он автоматом переопределится, даже если и был
        self.rcond_sims[old_cid] |= {cid}  # ну и в обратное добавим новый

    def build_tree(self):
        set(self.cond_sims.keys()) | set(self.cond_sims.values())
        tree = defaultdict(dict)
        # Группируем родителей по детям
        for child, par in self.cond_sims.items():
            tree[par] |= {child: {}}  # todo: make from self.rcond_sim

        # Строим дерево снизу вверх
        def subtree(node):
            if not node:
                return node
            for key in node:
                subnode = tree.pop(key, {})
                d = subtree(subnode)
                node[key] |= d  # actual tree rebuilding here!
            return node  # todo: refact?

        # Находим корни / без родителей
        roots = set(self.cond_sims.values()) - set(self.cond_sims.keys())
        for root in roots:
            _ = subtree(tree[root])

        self.tree = tree


def get_sim(s1, s2) -> int:
    sim = SequenceMatcher(None, s1, s2).ratio() - 0.6
    return int(sim * 10_000) if sim > 0 else 0


def clean(s) -> str:
    clear = r"[^\w\s.,!?;:()\-]"
    repeat = r"(.)\1{2,}"
    s = re.sub(clear, "", s).lower()
    s = re.sub(repeat, r"\1", s)
    return s.replace("\n\n", "\n").replace("  ", " ").strip(" \n/.,!?-")
