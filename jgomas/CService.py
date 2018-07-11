from spade.agent import Agent
from spade.behaviour import Behaviour
from spade.template import Template


class CService(Agent):

    def __init__(self, jid="cservice@localhost", password="secret"):
        self.m_ServiceList = {}
        Agent.__init__(self, jid, password)

    def register_service(self, service_name, jid):
        if service_name in self.m_ServiceList:
            if self.m_ServiceList[service_name].count(jid) == 0:
                self.m_ServiceList[service_name].append(jid)
        else:
            self.m_ServiceList[service_name] = [jid]

    def deregister_service(self, service_name, jid):
        if service_name in self.m_ServiceList and self.m_ServiceList[service_name].count(jid) > 0:
            self.m_ServiceList[service_name].remove(jid)

    def deregister_agent(self, jid):
        for service in self.m_ServiceList:
            if jid in service:
                service.remove(jid)

    def get_service(self, service_name):
        if service_name in self.m_ServiceList:
            return self.m_ServiceList[service_name]
        else:
            return []

    def start(self, auto_register=True):

        class RegisterServiceBehaviour(Behaviour):
            async def run(self):
                msg = await self.receive(timeout=1000000)
                self.agent.register_service(msg.body, str(msg.sender.bare()))
                print("Service " + msg.body + " of " + msg.sender + " registered")

        class DeregisterServiceBehaviour(Behaviour):
            async def run(self):
                msg = await self.receive(timeout=1000000)
                self.agent.deregister_service(msg.body, msg.sender)
                print("Service " + msg.body + " of " + msg.sender + " deregistered")

        class DeregisterAgentBehaviour(Behaviour):
            async def run(self):
                msg = await self.receive(timeout=1000000)
                self.agent.deregister_agent(msg.sender)
                print("Agent " + msg.sender + " deregistered")

        class GetServiceBehaviour(Behaviour):
            async def run(self):
                msg = await self.receive(timeout=1000000)
                names = self.agent.get_service(msg.body)
                reply = msg.make_reply()
                reply.body = str(names)
                await self.send(reply)
                print("Services sended")

        Agent.start(self, auto_register=auto_register)
        template1 = Template()
        template1.set_metadata("performative", "register")
        self.add_behaviour(RegisterServiceBehaviour(), template1)

        template2 = Template()
        template2.set_metadata("performative", "deregister_service")
        self.add_behaviour(DeregisterServiceBehaviour(), template2)

        template3 = Template()
        template3.set_metadata("performative", "deregister_agent")
        self.add_behaviour(DeregisterAgentBehaviour(), template3)

        template4 = Template()
        template4.set_metadata("performative", "get")
        self.add_behaviour(GetServiceBehaviour(), template4)
