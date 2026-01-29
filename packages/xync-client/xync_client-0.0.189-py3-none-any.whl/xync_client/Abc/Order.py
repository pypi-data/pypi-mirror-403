from abc import abstractmethod

from xync_client.Abc.Agent import BaseAgentClient
from xync_schema.models import Order, PmEx, CredEx


class BaseOrderClient:
    order: Order
    agent_client: BaseAgentClient
    im_maker: bool
    im_seller: bool

    def __init__(self, order: Order, agent_client: BaseAgentClient):
        self.order = order
        self.im_maker = order.taker_id != agent_client.actor.id  # or order.ad.agent_id == agent.id
        self.im_seller = order.ad.pair_side.is_sell and self.im_maker
        self.agent_client = agent_client

    # 5: [B] Перевод сделки в состояние "оплачено", c отправкой чека
    async def mark_payed(self, cred_id: int = None, receipt: bytes = None):
        cred_id = cred_id or self.order.cred_id
        pmex = await PmEx.get(pm__pmcurs__id=self.order.cred.pmcur_id, ex=self.agent_client.ex_client.ex)
        credex = await CredEx.get(cred_id=cred_id, ex=self.agent_client.ex_client.ex)
        await self._mark_payed(credex.exid, pmex.exid, receipt)

    @abstractmethod
    async def _mark_payed(self, credex_exid: int = None, pmex_exid: int | str = None, receipt: bytes = None): ...

    # 6: [B] Отмена сделки
    @abstractmethod
    async def cancel_order(self) -> bool: ...

    # 6: Запрос отмены (оплаченная контрагентом продажа)
    async def cancel_request(self) -> bool: ...

    # 6: Одобрение запроса на отмену (оплаченная мной покупка)
    async def cancel_accept(self): ...

    # 7: [S] Подтвердить получение оплаты
    @abstractmethod
    async def confirm(self) -> bool: ...

    # 9, 10: [S, B] Подать аппеляцию cо скриншотом / видео / файлом
    @abstractmethod
    async def start_appeal(self, file) -> bool: ...

    # 11, 12: [S, B] Встречное оспаривание полученной аппеляции cо скриншотом / видео / файлом
    @abstractmethod
    async def dispute_appeal(self, file) -> bool: ...

    # 15: [B, S] Отмена аппеляции
    @abstractmethod
    async def cancel_appeal(self) -> bool: ...

    # 15: Принять аппеляцию
    async def appeal_accept(self): ...

    # 16: Отправка сообщения юзеру в чат по ордеру с приложенным файлом
    @abstractmethod
    async def send_order_msg(self, msg: str, file=None) -> bool: ...

    # 17: Отправка сообщения по апелляции
    @abstractmethod
    async def send_appeal_msg(self, file, msg: str = None) -> bool: ...
