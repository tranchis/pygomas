from loguru import logger
from spade.behaviour import OneShotBehaviour
from . import POWER_UNIT
from .medicpack import MedicPack
from .bditroop import BDITroop, CLASS_MEDIC
from .config import MEDIC_SERVICE
import random
from agentspeak import Actions
from agentspeak.stdlib import actions as asp_action


class BDIMedic(BDITroop):
    packs_delivered = 0
    medic_pack_offset = 5

    def __init__(self, *args, **kwargs):
        medic_actions = Actions(asp_action)

        @medic_actions.add(".cure", 0)
        def _cure(agent, term, intention):
            class CreateMedicPackBehaviour(OneShotBehaviour):
                async def run(self):
                    await self.agent.create_medic_pack()

            b = CreateMedicPackBehaviour()
            self.add_behaviour(b)
            yield

        super().__init__(actions=medic_actions, *args, **kwargs)
        self.services.append(MEDIC_SERVICE)
        self.eclass = CLASS_MEDIC

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
        logger.info("{} Creating medic packs.".format(self.name))
        while self.perform_medic_action():
            BDIMedic.packs_delivered += 1
            name = "medicpack{}@{}".format(BDIMedic.packs_delivered, self.jid.domain)
            x = self.movement.position.x + random.random() * BDIMedic.medic_pack_offset
            z = self.movement.position.z + random.random() * BDIMedic.medic_pack_offset

            while not self.check_static_position(x, z):
                x = self.movement.position.x + random.random() * BDIMedic.medic_pack_offset
                z = self.movement.position.z + random.random() * BDIMedic.medic_pack_offset
            team = self.team

            try:
                pack = MedicPack(name=name, passwd="secret", x=x, z=z, team=team, manager_jid=self.manager)
                await pack.start()
            except Exception as e:
                logger.warning("Medic {} could not create MedicPack: {}".format(self.name, e))
