import json

from loguru import logger

from spade.template import Template
from spade.behaviour import CyclicBehaviour, OneShotBehaviour

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
        # self.launch_cfa_responder_behaviour()
        @self.bdi_actions.add(".reload", 0)
        def _cure(agent, term, intention):
            class CreateAmmoPackBehaviour(OneShotBehaviour):
                async def run(self):
                    await self.agent.create_ammo_pack()

            b = CreateAmmoPackBehaviour()
            self.add_behaviour(b)
            yield

    def perform_ammo_action(self):
        # We can give ammo paks if we have power enough...
        if self.get_power() >= POWER_UNIT:
            self.use_power()
            return True
        return False

    async def create_ammo_pack(self):
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
                await pack.start()
            except Exception as e:
                logger.warning(
                    "FieldOps {} could not create AmmoPack: {}".format(self.name, e))

            packs_delivered += 1
            logger.info("AmmoPack {} created.".format(name))

        return packs_delivered
