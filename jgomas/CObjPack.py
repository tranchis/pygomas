from spade.behaviour import Behaviour
from jgomas.CPack import CPack
from jgomas.Vector3D import Vector3D
from spade.template import Template


class CObjPack(CPack):

    def SetTaken(self, _bTaken):
        self.m_bTaken = _bTaken

    def start(self):
        CPack.start(self)
        self.m_bTaken = False
        self.m_eType = self.PACK_OBJPACK
        self.m_Origin = Vector3D()
        self.m_Origin.x = self.m_Position.x
        self.m_Origin.y = self.m_Position.y
        self.m_Origin.z = self.m_Position.z
        t = Template()
        t.set_metadata("performative", "inform")
        self.add_behaviour(self.PackLostResponderBehaviour(), t)

    def PerformPackTaken(self, _sContent):
        print("[" + self.name + "]: Objective Taken!!")

        tokens = _sContent.split()
        sTeam = tokens[5]

        if sTeam.upper() == "AXIS":
            self.m_bTaken = False
            self.m_Position.x = self.m_Origin.x
            self.m_Position.y = self.m_Origin.y
            self.m_Position.z = self.m_Origin.z
        else:
            self.m_bTaken = True

    class PackLostResponderBehaviour(Behaviour):
        async def run(self):
            msg = await self.receive(timeout=1000000)
            if msg:
                self.m_bTaken = False
                sContent = msg.body
                tokens = sContent.split()
                self.agent.m_Position.x = float(tokens[2])
                self.agent.m_Position.y = float(tokens[4])
                self.agent.m_Position.z = float(tokens[6])
