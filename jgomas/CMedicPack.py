from spade.behaviour import TimeoutBehaviour
from jgomas.CPack import CPack
from datetime import datetime
from spade.message import Message


now = datetime.now


class CMedicPack(CPack):

    def start(self):

        self.m_eType = CPack.PACK_MEDICPACK

        CPack.start(self)

        self.addBehaviour(self.AutoDestroyBehaviour(now()+25))

    def PerformPackTaken(self, _sContent):
        self._kill()

    class AutoDestroyBehaviour(TimeoutBehaviour):
        async def run(self):
            msg = Message(to=self.m_Manager)
            msg.set_metadata("performative", "inform")
            msg.body = "ID: " + self.agent.name + " DESTROY "
            await self.send(msg)
            self.agent._kill()