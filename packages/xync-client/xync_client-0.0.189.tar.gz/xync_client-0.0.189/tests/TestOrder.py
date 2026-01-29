import pytest

from xync_schema.models import Agent, Order

from xync_client.Abc.Ex import BaseExClient
from xync_client.Abc.Order import BaseOrderClient
from xync_client.Abc.BaseTest import BaseTest
from xync_client.loader import PRX


@pytest.mark.asyncio(loop_scope="session")
class TestOrder(BaseTest):
    exid: int = 2013140873197371392

    @pytest.fixture(scope="class", autouse=True)
    async def clients(self) -> BaseOrderClient:
        order = await Order.get(exid=self.exid).prefetch_related("ad__pair_side")
        if not (agent := await Agent.get_or_none(actor_id=order.ad.maker_id)):
            agent = await Agent.get(actor_id=order.taker_id)
        await agent.fetch_related("actor__ex", "actor__person__user__gmail")
        prx = PRX and "http://" + PRX
        ex_client: BaseExClient = agent.actor.ex.client(proxy=prx)
        agent_client: BaseOrderClient = agent.client(ex_client, proxy=prx)
        order_client = order.client(agent_client)
        yield order_client
        await agent_client.stop()

    # async def test_cancel_accept(self, clients: BaseOrderClient):
    #     res = await clients.cancel_accept()
    #     assert res, f"cancel_accept failed: {res}"
    #
    # async def test_appeal_accept(self, clients: BaseOrderClient):
    #     res = await clients.appeal_accept()
    #     assert res, f"appeal_accept failed: {res}"
    #
    # async def test_start_completed_order_appeal(self, clients: BaseOrderClient):
    #     res = await clients.start_completed_order_appeal()  # by taker
    #     assert res, f"appeal_accept failed: {res}"
