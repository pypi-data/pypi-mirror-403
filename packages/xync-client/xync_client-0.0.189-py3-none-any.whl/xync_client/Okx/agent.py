from xync_client.Abc.Agent import BaseAgentClient
from asyncio import run
from x_model import init_db
from xync_schema.models import Agent, Ex

from xync_client.Okx.ex import ExClient


class AgentClient(BaseAgentClient):
    async def my_fiats(self):
        response = await self._get("/v3/c2c/receiptAccounts")
        fiats = response["data"]
        return {
            fiat["type"]: field["value"] for fiat in fiats for field in fiat["fields"] if field["key"] == "accountNo"
        }


async def main():
    from xync_client.loader import TORM

    _cn = await init_db(TORM)
    ex = await Ex.get(name="Okx")
    agent = await Agent.get(actor__ex=ex).prefetch_related("actor__ex", "actor__person__user__gmail")
    ecl: ExClient = ex.client()
    cl = agent.client(ecl)

    _fiats = await cl.my_fiats()

    await cl.stop()


if __name__ == "__main__":
    run(main())
