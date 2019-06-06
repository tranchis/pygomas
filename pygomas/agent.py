import json
from spade_bdi.bdi import BDIAgent

from loguru import logger

from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message

from .ontology import PERFORMATIVE, PERFORMATIVE_REGISTER_SERVICE, PERFORMATIVE_DEREGISTER_SERVICE, \
    PERFORMATIVE_DEREGISTER_AGENT, NAME, TEAM

LONG_RECEIVE_WAIT: int = 1000000


class AbstractAgent(Agent):
    def __init__(self, jid, passwd="secret", team=0, service_jid="cservice@localhost", verify_security=False):
        self.services = list()
        self._name = jid
        self.position_x = None
        self.position_z = None
        self.team = team
        self.service_jid = service_jid

        super().__init__(jid=jid, password=passwd, verify_security=verify_security)

    def start(self, auto_register=True):
        future = super().start(auto_register=auto_register)
        if self.services:
            for service in self.services:
                logger.info("{} registering service {}".format(
                    self.name, service))
                self.register_service(service)
        return future

    async def die(self):
        await self.deregister_agent()
        await self.stop()
        logger.info("Agent {} was stopped.".format(self.name))

    def register_service(self, service_name):
        class RegisterBehaviour(OneShotBehaviour):
            async def run(self):
                msg = Message(to=self.agent.service_jid)
                msg.set_metadata(PERFORMATIVE, PERFORMATIVE_REGISTER_SERVICE)
                msg.body = json.dumps(
                    {NAME: service_name, TEAM: self.agent.team})
                await self.send(msg)

        self.add_behaviour(RegisterBehaviour())

    def deregister_service(self, service_name):
        class DeregisterBehaviour(OneShotBehaviour):
            async def run(self):
                msg = Message(to=self.agent.service_jid)
                msg.set_metadata(PERFORMATIVE, PERFORMATIVE_DEREGISTER_SERVICE)
                msg.body = json.dumps(
                    {NAME: service_name, TEAM: self.agent.team})
                await self.send(msg)

        self.add_behaviour(DeregisterBehaviour())

    async def deregister_agent(self):
        class DeregisterAgentBehaviour(OneShotBehaviour):
            async def run(self):
                msg = Message(to=self.agent.service_jid)
                msg.set_metadata(PERFORMATIVE, PERFORMATIVE_DEREGISTER_AGENT)
                await self.send(msg)

        behav = DeregisterAgentBehaviour()
        self.add_behaviour(behav)
        # await behav.join(timeout=5)

    @property
    def name(self):
        return self._name
