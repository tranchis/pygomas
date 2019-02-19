from loguru import logger

from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message

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
                logger.info("   * Name: " + self.name)
                logger.info("   * Type: " + service)
                self.register_service(service)
        return future

    def stop(self, timeout=5):
        self.deregister_agent()
        super().stop(timeout=timeout)

    def register_service(self, service_name):
        class RegisterBehaviour(OneShotBehaviour):
            async def run(self):
                msg = Message(to=self.agent.service_jid)
                msg.set_metadata("performative", "register")
                msg.body = service_name
                await self.send(msg)

        self.add_behaviour(RegisterBehaviour())

    def deregister_service(self, service_name):
        class DeregisterBehaviour(OneShotBehaviour):
            async def run(self):
                msg = Message(to=self.agent.service_jid)
                msg.set_metadata("performative", "deregister_service")
                msg.body = service_name
                await self.send(msg)

        self.add_behaviour(DeregisterBehaviour())

    def deregister_agent(self):
        class DeregisterAgentBehaviour(OneShotBehaviour):
            async def run(self):
                msg = Message(to=self.agent.service_jid)
                msg.set_metadata("performative", "deregister_agent")
                await self.send(msg)

        self.add_behaviour(DeregisterAgentBehaviour())

    @property
    def name(self):
        return self._name
