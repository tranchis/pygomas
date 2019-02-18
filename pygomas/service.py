import json

from loguru import logger

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template


class Service(Agent):

    def __init__(self, jid="cservice@localhost", password="secret"):
        self.services = {}
        super().__init__(jid=jid, password=password)

    def register_service(self, service_name, jid):
        if service_name in self.services:
            if self.services[service_name].count(jid) == 0:
                self.services[service_name].append(jid)
        else:
            self.services[service_name] = [jid]

    def deregister_service(self, service_name, jid):
        if service_name in self.services and self.services[service_name].count(jid) > 0:
            self.services[service_name].remove(jid)

    def deregister_agent(self, jid):
        for service in self.services:
            if jid in service:
                service.remove(jid)

    def get_service(self, service_name):
        logger.info("get service '{}'".format(service_name))
        if service_name in self.services:
            logger.info("I got service")
            return self.services[service_name]
        else:
            logger.info("No service")
            return []

    async def setup(self):
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


class RegisterServiceBehaviour(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=1000000)
        self.agent.register_service(msg.body, str(msg.sender.bare()))
        logger.info("Service " + msg.body + " of " + str(msg.sender) + " registered")


class DeregisterServiceBehaviour(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=1000000)
        self.agent.deregister_service(msg.body, msg.sender)
        logger.info("Service " + msg.body + " of " + str(msg.sender) + " deregistered")


class DeregisterAgentBehaviour(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=1000000)
        self.agent.deregister_agent(str(msg.sender))
        logger.info("Agent " + str(msg.sender) + " deregistered")


class GetServiceBehaviour(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=1000000)
        logger.info("Requesting service {}".format(msg.body))
        names = self.agent.get_service(msg.body)
        reply = msg.make_reply()
        reply.body = json.dumps(names)
        await self.send(reply)
        logger.info("Services sent: {}".format(reply.body))
