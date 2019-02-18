from loguru import logger

from spade.template import Template
from spade.behaviour import CyclicBehaviour
from .ammopack import AmmoPack
from .troop import Troop, CLASS_FIELDOPS
from pygomas.ontology import AMMO_SERVICE
from .task import TASK_WALKING_PATH, TASK_PATROLLING, TASK_GOTO_POSITION, TASK_RUN_AWAY, TASK_ATTACK, \
    TASK_GET_OBJECTIVE, TASK_GIVE_BACKUP, TASK_GIVE_AMMOPACKS, TASK_GIVE_MEDICPAKS, TASK_NONE

import time


class FieldOps(Troop):
    """
    inner variable used to name packs
    """
    packs_delivered = 0

    '''
      'setup' method of SPADE agents.
     
      This method perform actions in common to CFieldOps agents (and derived classes)
      and calls parent's setup.
     
    '''

    #def start(self, auto_register=True):
    async def setup(self):
        self.services.append(AMMO_SERVICE)
        self.eclass = CLASS_FIELDOPS

        #super().start(auto_register=auto_register)

        self.launch_cfa_responder_behaviour()

    def setup_priorities(self):

        self.task_priority[TASK_NONE] = 0
        self.task_priority[TASK_GIVE_MEDICPAKS] = 0
        self.task_priority[TASK_GIVE_AMMOPACKS] = 2000
        self.task_priority[TASK_GIVE_BACKUP] = 0
        self.task_priority[TASK_GET_OBJECTIVE] = 1000
        self.task_priority[TASK_ATTACK] = 1000
        self.task_priority[TASK_RUN_AWAY] = 1500
        self.task_priority[TASK_GOTO_POSITION] = 750
        self.task_priority[TASK_PATROLLING] = 500
        self.task_priority[TASK_WALKING_PATH] = 750

    # Behaviours to handle calls for services we offer

    # Call For Ammo
    def launch_cfa_responder_behaviour(self):
        class CallForAmmoResponderBehaviour(CyclicBehaviour):
            async def run(self):
                msg = await self.receive(timeout=100000)
                if msg:
                    owner = msg.sender
                    content = msg.body

                    if self.agent.check_ammo_action(content):
                        self.agent.add_task(TASK_GIVE_AMMOPACKS, owner, content)

        # Behaviour to handle a Call For Backup request
        template = Template()
        template.set_metadata("performative", "cfa")
        self.add_behaviour(CallForAmmoResponderBehaviour(), template)

    '''
     Decides if agent accepts the CFA request
     
     This method is a decision function invoked when a CALL FOR AMMO request has arrived.
     Parameter sContent is the content of message received in CFA responder behaviour as
     result of a CallForAmmo request, so it must be: ( x , y , z ) ( ammo ).
     By default, the return value is TRUE, so agents always accept all CFA requests.
     
      It's very useful to overload this method.
      @param _sContent
      @return TRUE
     '''

    def check_ammo_action(self, content):
        # We always go to help (we are like Mother Teresa of Calcutta)
        return True

    # /////////////////////////////////////////////////////////////////////////////////////////////////////

    # /////////////////////////////////////////////////////////////////////////////////////////////////////
    def perform_ammo_action(self):
        # We can give ammo paks if we have power enough...
        if self.get_power() >= 25:
            self.use_power()
            return True
        return False

    # /////////////////////////////////////////////////////////////////////////////////////////////////////

    # /////////////////////////////////////////////////////////////////////////////////////////////////////
    '''
     Action to do when this agent reaches the target of current task.
     
     This method is called when this agent goes to state TARGET_REACHED. If current task is TASK_GIVE_AMMOPACKS,
     agent must give ammo packs, but in other case, it calls to parent's method.
     
     It's very useful to overload this method.
     
     @param _CurrentTask
     '''

    def perform_target_reached(self, current_task):

        if current_task.type == TASK_NONE:
            pass

        elif current_task.type == TASK_GIVE_AMMOPACKS:
            packs_delivered = self.create_ammo_pack()
            current_task.packs_delivered += packs_delivered

        else:
            super().perform_target_reached(current_task)

    # /////////////////////////////////////////////////////////////////////////////////////////////////////

    # /////////////////////////////////////////////////////////////////////////////////////////////////////
    '''/**
     * Creates ammo packs if possible.
     *
     * This method allows to create medic packs if there is enough power in the agent's power bar.
     *
     * @return iPacksDelivered: number of ammo packs created
     *
     */'''

    def create_ammo_pack(self):

        packs_delivered = 0
        while self.perform_ammo_action():
            # if we give ammo paks, need inform to that agent?
            FieldOps.packs_delivered += 1
            name = "ammopack" + str(FieldOps.packs_delivered) + "@" + self.jid.domain
            x = self.movement.position.x / 8
            z = self.movement.position.z / 8
            team = self.team

            pack = AmmoPack(name=name, passwd="secret", x=x, z=z, team=team, manager_jid=self.manager)
            pack.start()

            # time.sleep(0.5)
            packs_delivered += 1
            logger.info("AmmoPack created!!")

        return packs_delivered
