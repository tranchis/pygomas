import json

from loguru import logger

from spade.template import Template
from spade.behaviour import CyclicBehaviour, OneShotBehaviour

from . import POWER_UNIT
from .agent import LONG_RECEIVE_WAIT
from .bditroop import BDITroop, CLASS_MEDIC
from .ontology import MEDIC_SERVICE, PERFORMATIVE, PERFORMATIVE_CFM
from .task import TASK_NONE, TASK_GIVE_MEDICPAKS, TASK_GIVE_AMMOPACKS, TASK_GIVE_BACKUP, TASK_GET_OBJECTIVE, \
    TASK_ATTACK, TASK_RUN_AWAY, TASK_GOTO_POSITION, TASK_PATROLLING, TASK_WALKING_PATH
from .medicpack import MedicPack


class Medic(BDITroop):
    packs_delivered = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.services.append(MEDIC_SERVICE)
        self.eclass = CLASS_MEDIC

    async def setup(self):
        # self.launch_cfm_responder_behaviour()

        @self.bdi_actions.add(".cure", 0)
        def _cure(agent, term, intention):
            class CreateMedicPackBehaviour(OneShotBehaviour):
                async def run(self):
                    await self.agent.create_medic_pack()

            b = CreateMedicPackBehaviour()
            self.add_behaviour(b)
            print("Creating medic pack")
            yield

    # def setup_priorities(self):
    #     self.task_manager.set_priority(TASK_NONE, 0)
    #     self.task_manager.set_priority(TASK_GIVE_MEDICPAKS, 2000)
    #     self.task_manager.set_priority(TASK_GIVE_AMMOPACKS, 0)
    #     self.task_manager.set_priority(TASK_GIVE_BACKUP, 0)
    #     self.task_manager.set_priority(TASK_GET_OBJECTIVE, 1000)
    #     self.task_manager.set_priority(TASK_ATTACK, 1000)
    #     self.task_manager.set_priority(TASK_RUN_AWAY, 1500)
    #     self.task_manager.set_priority(TASK_GOTO_POSITION, 750)
    #     self.task_manager.set_priority(TASK_PATROLLING, 500)
    #     self.task_manager.set_priority(TASK_WALKING_PATH, 750)

    # Behaviours to handle calls for services we offer

    # Call For Medic
    # def launch_cfm_responder_behaviour(self):
    #     class CallForMedicResponderBehaviour(CyclicBehaviour):
    #         async def run(self):
    #             msg = await self.receive(timeout=LONG_RECEIVE_WAIT)
    #             if msg:
    #                 owner = msg.sender
    #                 content = json.loads(msg.body)
    #                 logger.info("{} got a call for medic from {}: {}".format(
    #                     self.agent.name, owner, content))
    #                 if self.agent.check_medic_action(content):
    #                     self.agent.task_manager.add_task(
    #                         TASK_GIVE_MEDICPAKS, owner, content)
    #                     # es expulsiva?

    #     # Behaviour to handle a Call For Backup request
    #     template = Template()
    #     template.set_metadata(PERFORMATIVE, PERFORMATIVE_CFM)
    #     self.add_behaviour(CallForMedicResponderBehaviour(), template)

    def check_medic_action(self, content):
        """
        Decides if agent accepts the CFM request

        This method is a decision function invoked when a CALL FOR MEDIC request has arrived.

        It's very useful to overload this method.

        @param content: content of message received in CFM responder behaviour as
        result of a CallForMedic request, so it must be: ( x , y , z ) ( health )
        :returns: By default, the return value is True, so agents always accept all CFM requests.
        """
        # We always go to help (we are like Mother Teresa of Calcutta)
        return True

    def perform_medic_action(self):
        # We can give medic paks if we have power enough...
        if self.get_power() >= POWER_UNIT:
            self.use_power()
            return True

        return False

    def perform_target_reached(self, current_task):
        """
        Action to do when this agent reaches the target of current task.

        This method is called when this agent goes to state TARGET_REACHED. If current task is TASK_GIVE_MEDICPAKS,
        agent must give medic packs, but in other case, it calls to parent's method.

        It's very useful to overload this method.
        """
        if current_task.type == TASK_NONE:
            pass
        elif current_task.type == TASK_GIVE_MEDICPAKS:
            packs_delivered = self.create_medic_pack()
            # current_task.packs_delivered += packs_delivered
            logger.error("{} delivered {} medic packs.".format(
                self.name, packs_delivered))

        else:
            super().perform_target_reached(current_task)

    async def create_medic_pack(self):
        """
        Creates medic packs if possible.

        This method allows to create medic packs if there is enough power in the agent's power bar.

        :returns number of medic packs created
        """
        packs_delivered = 0
        logger.info("{} Creating medic packs.".format(self.name))
        while self.perform_medic_action():
            Medic.packs_delivered += 1
            name = "medicpack{}@{}".format(
                Medic.packs_delivered, self.jid.domain)

            x = self.movement.position.x
            z = self.movement.position.z
            team = self.team

            try:
                pack = MedicPack(name=name, passwd="secret",
                                 x=x, z=z, team=team, manager_jid=self.manager)
                await pack.start()
            except Exception as e:
                logger.warning(
                    "Medic {} could not create MedicPack: {}".format(self.name, e))

            packs_delivered += 1

        return packs_delivered
