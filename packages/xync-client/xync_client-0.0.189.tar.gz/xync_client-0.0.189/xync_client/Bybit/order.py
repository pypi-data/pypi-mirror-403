from asyncio import sleep

from bybit_p2p._exceptions import FailedRequestError
from xync_client.Bybit.agent import AgentClient

from xync_client.Abc.Order import BaseOrderClient


class OrderClient(BaseOrderClient):
    agent_client: AgentClient

    # 5: Перевод сделки в состояние "оплачено", c отправкой чека
    async def _mark_payed(self, credex_exid: int = None, pmex_exid: int | str = None, receipt: bytes = None):
        params = dict(orderId=str(self.order.exid), paymentType=str(pmex_exid), paymentId=str(credex_exid))
        try:
            self.agent_client.api.mark_as_paid(**params)
        except FailedRequestError as e:
            if e.status_code == 912100202:  # Server error, please try again later
                await sleep(5, self.agent_client.api.mark_as_paid(**params))
            else:
                raise e

    # 7: Подтвердить получение оплаты
    async def confirm(self):
        try:
            res = self.agent_client.api.release_assets(orderId=str(self.order.exid))
        except FailedRequestError as e:
            if e.status_code == 912100202:  # Server error, please try again later
                await sleep(5)
                res = self.agent_client.api.release_assets(orderId=str(self.order.exid))
            else:
                raise e
        return res

    # 6: Отмена одобренной сделки
    async def cancel(self) -> bool: ...

    # 6: Запрос отмены (оплаченная контрагентом продажа)
    async def cancel_request(self) -> bool: ...

    # 6: Одобрение запроса на отмену (оплаченная мной покупка)
    async def cancel_accept(self) -> bool:
        data = {"orderId": str(self.order.exid), "examineResult": "PASS"}
        res = await self.agent_client._post("/x-api/fiat/otc/order/buyer/examine/sellerCancelOrderApply", data)
        return res["ret_code"] == 0

    # 9, 10: Подать аппеляцию cо скриншотом/видео/файлом
    async def start_appeal(self, file: bytes = None) -> bool:
        data = {"orderId": str(self.order.exid), "appealType": "3"}
        await self.agent_client._post("/x-api/fiat/otc/order/appealpreconsult", data)
        data = {
            "appealProof": "/fiat/p2p/oss/show/otc/9001/539335388KVGD-HEoEIAGExJK1xLnVFDUeyHzRmQJtCUE-nrCcYc.png?e=1769148296&token=T6PnzVD38SrwGUpGxOnuxeeuk0w9NJ9AYAnkZgKg04k=&salt=f11dd26f5b224c6eb1a468b73286b748",
            "orderId": str(self.order.exid),
            "appealType": "3",
            "appealContent": "",
            "selectOption": 2,
            "windowType": None,
        }
        await self.agent_client._post("/x-api/fiat/otc/order/appealwithconsult", data)

    # 9, 10: Подать аппеляцию cо скриншотом/видео/файлом
    async def start_completed_order_appeal(self, file: bytes = None) -> bool:
        data = {
            "appealProof": "/fiat/p2p/oss/show/otc/9001/539335388K0zO0qQnis9_uldMYcsrBzQsiJYraPQMZUV-oAtmtt4.png?e=1769235078&token=I6LHvlNUVLyGLlHeBMNhWRC96xtOH_syMzMv1MICpi4=&salt=df86934924f34d8e8912d3779f0f78a7",
            "orderId": str(self.order.exid),
            "appealType": "13",  # тейкер покупатель начал апил по завершенному ордеру
            "appealContent": "не отвечает",
            "actualAmount": None,
        }
        res = await self.agent_client._post("/x-api/fiat/otc/completeOrder/appeal", data)
        return res["ret_code"] == 0

    # 11, 12: Встречное оспаривание полученной аппеляции cо скриншотом/видео/файлом
    async def dispute_appeal(self, file) -> bool: ...

    # 15: Отмена аппеляции
    async def cancel_appeal(self) -> bool: ...

    # 15: Отмена аппеляции
    async def cancel_completed_order_appeal(self) -> bool:
        data = {"orderId": str(self.order.exid)}
        # Отменить свою аппеляцию: я продавец, открыл апеляцию по готовому ордеру, теперь отменяю ее обратно
        res = await self.agent_client._post("/x-api/fiat/otc/completeOrder/cancel_appeal", data)
        return res["ret_code"] == 0

    async def appeal_accept(self) -> bool:
        data = {"orderId": str(self.order.exid)}
        # Принять аппеляцию: я покупатель, прожал оплачено, продавец оспорил, я согл, ордер отменится
        res = await self.agent_client._post("/x-api/fiat/otc/order/cancelAfterCustomerNegotiation", data)
        return res["ret_code"] == 0

    # 16: Отправка сообщения юзеру в чат по ордеру с приложенным файлом
    async def send_order_msg(self, msg: str, file=None) -> bool: ...

    # 17: Отправка сообщения по апелляции
    async def send_appeal_msg(self, file, msg: str = None) -> bool: ...

    # Загрузка файла
    async def _upload_file(self, order_id: int, path_to_file: str): ...
