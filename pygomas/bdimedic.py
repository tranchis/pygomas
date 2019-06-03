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
        @self.bdi_actions.add(".cure", 0)
        def _cure(agent, term, intention):
            class CreateMedicPackBehaviour(OneShotBehaviour):
                async def run(self):
                    await self.agent.create_medic_pack()

            b = CreateMedicPackBehaviour()
            self.add_behaviour(b)
            yield

    def perform_medic_action(self):
        # We can give medic paks if we have power enough...
        if self.get_power() >= POWER_UNIT:
            self.use_power()
            return True

        return False

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
