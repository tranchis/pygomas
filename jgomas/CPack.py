import random
from spade.message import Message
from jgomas.CJGomasAgent import CJGomasAgent
from jgomas.Vector3D import Vector3D
from spade.behaviour import OneShotBehaviour, Behaviour
from spade.template import Template


class CPack(CJGomasAgent):

    PACK_NONE = 1000
    PACK_MEDICPACK = 1001
    PACK_AMMOPACK = 1002
    PACK_OBJPACK = 1003

    pack_name = {
        PACK_NONE: 'NONE',
        PACK_MEDICPACK: 'MEDIC',
        PACK_AMMOPACK: 'AMMO',
        PACK_OBJPACK: 'OBJ'
    }

    def __str__(self):
        return "P(" + str(self.pack_name[self.m_eType]) +\
               "," + str(self.m_Position) + ")"

    def __init__(self, name, passwd="secret", manager_jid="cmanager@localhost", x=0, z=0, team=0):

        CJGomasAgent.__init__(self, name, passwd, team)
        self.m_eType = self.PACK_NONE
        self.m_Manager = manager_jid

        self.m_Position = Vector3D()
        self.m_Position.x = (x * 8)
        self.m_Position.y = 0
        self.m_Position.z = (z * 8)

        self.m_eTeam = team

    def start(self):

        CJGomasAgent.start(self)
        if self.m_eType != self.PACK_OBJPACK:
            dOffset = 10.0  # OJO
            self.m_Position.x += random.random() * dOffset
            self.m_Position.z += random.random() * dOffset

        self.add_behaviour(self.CreatePackBehaviour())

        t = Template()
        t.set_metadata("performative", "pack")
        self.add_behaviour(self.PackTakenResponderBehaviour(), t)

    class CreatePackBehaviour(OneShotBehaviour):
        async def run(self):
            msg = Message(to=self.agent.m_Manager)
            msg.set_metadata("performative", "pack")
            msg.body = "NAME: " + self.agent.name + " CREATE TYPE: " + str(self.agent.m_eType) + " TEAM: " + str(self.agent.m_eTeam) + " ( " + str(self.agent.m_Position.x) + " , " + str(self.agent.m_Position.y) + " , " + str(self.agent.m_Position.z) + " ) "
            await self.send(msg)

    class PackTakenResponderBehaviour(Behaviour):
        async def run(self):
            msg = await self.receive(timeout=1000000)
            if msg is not None:
                self.myAgent.PerformPackTaken(msg.getContent())

    def takeDown(self):
        pass

    # virtual function for overloading
    def PerformPackTaken(self, _sContent):
        pass
