from asyncio import create_task
from pyro_client.client.file import FileClient
from xync_bot import XyncBot
from xync_client.Abc.InAgent import BaseInAgentClient
from xync_schema.models import Agent

from xync_client.Bybit.agent import AgentClient
from xync_client.Bybit.ex import ExClient

from xync_schema import models

from xync_client.Bybit.etype.order import OrderItem


class InAgentClient(BaseInAgentClient):
    agent_client: AgentClient

    orders: dict[int, models.Order] = {}

    def __init__(self, agent: Agent, ex_client: ExClient, fbot: FileClient, bbot: XyncBot, **kwargs):
        super().__init__(agent, ex_client, fbot, bbot, **kwargs)
        create_task(self.load_pending_orders())

    async def load_pending_orders(self):
        po: dict[int, OrderItem] = await self.get_pending_orders()
        if isinstance(po, int):  # если код ошибки вместо результата
            raise ValueError(po)
        self.orders = {o.exid: o for o in await models.Order.filter(exid__in=po.keys())}
        for oid in po.keys() - self.orders.keys():
            fo = self.api.get_order_details(orderId=oid)
            self.orders[oid] = await self.order_save(fo)
