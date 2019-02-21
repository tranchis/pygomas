import random
from loguru import logger

from .ontology import PERFORMATIVE, PERFORMATIVE_PACK
from .agent import AbstractAgent, LONG_RECEIVE_WAIT
from .vector import Vector3D
from spade.message import Message
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.template import Template

PACK_NONE = 1000
PACK_MEDICPACK = 1001
PACK_AMMOPACK = 1002
PACK_OBJPACK = 1003

PACK_NAME = {
    PACK_NONE: 'NONE',
    PACK_MEDICPACK: 'MEDIC',
    PACK_AMMOPACK: 'AMMO',
    PACK_OBJPACK: 'OBJ'
}


class Pack(AbstractAgent):

    def __str__(self):
        return "P(" + str(PACK_NAME[self.type]) + "," + str(self.position) + ")"

    def __init__(self, name, passwd="secret", manager_jid="cmanager@localhost", x=0, z=0, team=0):

        super().__init__(name, passwd, team)
        self.type = PACK_NONE
        self.manager = manager_jid

        self.position = Vector3D()
        self.position.x = (x * 8)
        self.position.y = 0
        self.position.z = (z * 8)

        self.team = team

    async def setup(self):
        if self.type != PACK_OBJPACK:
            offset = 10.0  # WARN
            self.position.x += random.random() * offset
            self.position.z += random.random() * offset

        self.add_behaviour(self.CreatePackBehaviour())

        t = Template()
        t.set_metadata(PERFORMATIVE, PERFORMATIVE_PACK)
        self.add_behaviour(self.PackTakenResponderBehaviour(), t)

    class CreatePackBehaviour(OneShotBehaviour):
        async def run(self):
            msg = Message(to=self.agent.manager)
            msg.set_metadata(PERFORMATIVE, PERFORMATIVE_PACK)
            msg.body = "NAME: " + self.agent.name + " CREATE TYPE: " + str(self.agent.type) + " TEAM: " + str(
                self.agent.team) + " ( " + str(self.agent.position.x) + " , " + str(
                self.agent.position.y) + " , " + str(self.agent.position.z) + " ) "
            await self.send(msg)
            logger.info("CreatePack msg sent: {}".format(msg))

    class PackTakenResponderBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=LONG_RECEIVE_WAIT)
            if msg is not None:
                logger.info("PACK TAKEN: {}".format(msg))
                self.agent.perform_pack_taken(msg.body)

    # virtual function for overloading
    def perform_pack_taken(self, content):
        pass
