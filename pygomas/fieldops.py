import json

from loguru import logger

from spade.template import Template
from spade.behaviour import CyclicBehaviour

from . import POWER_UNIT
from .agent import LONG_RECEIVE_WAIT
from .ammopack import AmmoPack
from .bditroop import BDITroop, CLASS_FIELDOPS
from pygomas.ontology import AMMO_SERVICE, PERFORMATIVE, PERFORMATIVE_CFA
from .task import TASK_WALKING_PATH, TASK_PATROLLING, TASK_GOTO_POSITION, TASK_RUN_AWAY, TASK_ATTACK, \
    TASK_GET_OBJECTIVE, TASK_GIVE_BACKUP, TASK_GIVE_AMMOPACKS, TASK_GIVE_MEDICPAKS, TASK_NONE


class FieldOps(BDITroop):
    packs_delivered = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.services.append(AMMO_SERVICE)
        self.eclass = CLASS_FIELDOPS

    async def setup(self):
        self.launch_cfa_responder_behaviour()

    def setup_priorities(self):

        self.task_manager.set_priority(TASK_NONE, 0)
        self.task_manager.set_priority(TASK_GIVE_MEDICPAKS, 0)
        self.task_manager.set_priority(TASK_GIVE_AMMOPACKS, 2000)
        self.task_manager.set_priority(TASK_GIVE_BACKUP, 0)
        self.task_manager.set_priority(TASK_GET_OBJECTIVE, 1000)
        self.task_manager.set_priority(TASK_ATTACK, 1000)
        self.task_manager.set_priority(TASK_RUN_AWAY, 1500)
        self.task_manager.set_priority(TASK_GOTO_POSITION, 750)
        self.task_manager.set_priority(TASK_PATROLLING, 500)
        self.task_manager.set_priority(TASK_WALKING_PATH, 750)

    # Behaviours to handle calls for services we offer

    # Call For Ammo
    def launch_cfa_responder_behaviour(self):
        class CallForAmmoResponderBehaviour(CyclicBehaviour):
            async def run(self):
                msg = await self.receive(timeout=LONG_RECEIVE_WAIT)
                if msg:
                    owner = msg.sender
                    content = json.loads(msg.body)

                    if self.agent.check_ammo_action(content):
                        self.agent.task_manager.add_task(
                            TASK_GIVE_AMMOPACKS, owner, content)

        # Behaviour to handle a Call For Backup request
        template = Template()
        template.set_metadata(PERFORMATIVE, PERFORMATIVE_CFA)
        self.add_behaviour(CallForAmmoResponderBehaviour(), template)

    def check_ammo_action(self, content):
        """
        Decides if agent accepts the CFA request
        This method is a decision function invoked when a CALL FOR AMMO request has arrived.

        It's very useful to overload this method.
        :param content: content of message received in CFA responder behaviour as
        result of a CallForAmmo request, so it must be: ( x , y , z ) ( ammo ).
        :returns By default, the return value is TRUE, so agents always accept all CFA requests.
        """

        # We always go to help
        return True

    def perform_ammo_action(self):
        # We can give ammo paks if we have power enough...
        if self.get_power() >= POWER_UNIT:
            self.use_power()
            return True
        return False

    def perform_target_reached(self, current_task):
        """
         Action to do when this agent reaches the target of current task.

         This method is called when this agent goes to state TARGET_REACHED. If current task is TASK_GIVE_AMMOPACKS,
         agent must give ammo packs, but in other case, it calls to parent's method.

         It's very useful to overload this method.
         """

        if current_task.type == TASK_NONE:
            pass

        elif current_task.type == TASK_GIVE_AMMOPACKS:
            packs_delivered = self.create_ammo_pack()
            # current_task.packs_delivered += packs_delivered
            logger.error("{} delivered {} ammo packs.".format(
                self.name, packs_delivered))

        else:
            super().perform_target_reached(current_task)

    def create_ammo_pack(self):
        """
        Creates ammo packs if possible.

        This method allows to create medic packs if there is enough power in the agent's power bar.

        :returns number of ammo packs created
        """

        packs_delivered = 0
        logger.info("{} Creating ammo packs.".format(self.name))
        while self.perform_ammo_action():
            FieldOps.packs_delivered += 1
            name = "ammopack{}@{}".format(
                FieldOps.packs_delivered, self.jid.domain)
            x = self.movement.position.x
            z = self.movement.position.z
            team = self.team

            try:
                pack = AmmoPack(name=name, passwd="secret", x=x,
                                z=z, team=team, manager_jid=self.manager)
                pack.start()
            except Exception as e:
                logger.warning(
                    "FieldOps {} could not create AmmoPack: {}".format(self.name, e))

            packs_delivered += 1
            logger.info("AmmoPack {} created.".format(name))

        return packs_delivered
