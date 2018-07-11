from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message


class CJGomasAgent(Agent):
    def __init__(self, jid, passwd="secret", team=0, service_jid="cservice@localhost", verify_security=False):
        self.m_ServiceList = list()
        self._name = jid
        self.m_iPositionX = None
        self.m_iPositionZ = None
        self.m_eTeam = team
        self.service_jid = service_jid

        Agent.__init__(self, jid, passwd, verify_security)

    def start(self, auto_register=True):
        Agent.start(self, auto_register=auto_register)
        if self.m_ServiceList:
            for service in self.m_ServiceList:
                print("   * Name: " + self.name)
                print("   * Type: " + service)
                self.register_service(service)

    def take_down(self):
        self.deregister_agent()
        self.stop()

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
