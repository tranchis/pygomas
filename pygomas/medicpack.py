from datetime import datetime, timedelta
from .pack import Pack, PACK_MEDICPACK
from spade.behaviour import TimeoutBehaviour
from spade.message import Message

now = datetime.now


class MedicPack(Pack):

    async def setup(self):
        self.type = PACK_MEDICPACK
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
