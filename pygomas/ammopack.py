from spade.behaviour import TimeoutBehaviour
from .pack import Pack, PACK_AMMOPACK
from datetime import datetime, timedelta
from spade.message import Message

now = datetime.now


class AmmoPack(Pack):

    def start(self, auto_register=True):
        self.type = PACK_AMMOPACK

        super().start(auto_register)

        timeout = now() + timedelta(seconds=25)
        self.add_behaviour(self.AutoDestroyBehaviour(start_at=timeout))

    def perform_pack_taken(self, content):
        self.stop()

    class AutoDestroyBehaviour(TimeoutBehaviour):
        async def run(self):
            msg = Message(to=self.agent.m_Manager)
            msg.set_metadata("performative", "inform")
            msg.body = "ID: " + self.agent.name + " DESTROY "
            await self.send(msg)
            self.agent.stop()
