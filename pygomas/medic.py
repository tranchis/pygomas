from loguru import logger

from spade.template import Template
from spade.behaviour import CyclicBehaviour
from .troop import Troop, CLASS_MEDIC
from pygomas.ontology import MEDIC_SERVICE
from .task import TASK_NONE, TASK_GIVE_MEDICPAKS, TASK_GIVE_AMMOPACKS, TASK_GIVE_BACKUP, TASK_GET_OBJECTIVE, \
    TASK_ATTACK, TASK_RUN_AWAY, TASK_GOTO_POSITION, TASK_PATROLLING, TASK_WALKING_PATH
from .medicpack import MedicPack


class Medic(Troop):
    packs_delivered = 0
    """
    'setup' method of spade agents.
    
    This method perform actions in common to CMedic agents (and derived classes)
    and calls parent's setup.
    """

    #def start(self, auto_register=True):
    async def setup(self):
        self.services.append(MEDIC_SERVICE)
        self.eclass = CLASS_MEDIC
        #super().start(auto_register=auto_register)
        self.launch_cfm_responder_behaviour()

    def setup_priorities(self):
        self.task_priority[TASK_NONE] = 0
        self.task_priority[TASK_GIVE_MEDICPAKS] = 2000
        self.task_priority[TASK_GIVE_AMMOPACKS] = 0
        self.task_priority[TASK_GIVE_BACKUP] = 0
        self.task_priority[TASK_GET_OBJECTIVE] = 1000
        self.task_priority[TASK_ATTACK] = 1000
        self.task_priority[TASK_RUN_AWAY] = 1500
        self.task_priority[TASK_GOTO_POSITION] = 750
        self.task_priority[TASK_PATROLLING] = 500
        self.task_priority[TASK_WALKING_PATH] = 750

    # Behaviours to handle calls for services we offer

    # Call For Medic
    def launch_cfm_responder_behaviour(self):
        class CallForMedicResponderBehaviour(CyclicBehaviour):
            async def run(self):
                msg = await self.receive(timeout=100000)
                if msg:
                    owner = msg.sender
                    content = msg.body

                    if self.agent.check_medic_action(content):
                        self.agent.add_task(TASK_GIVE_MEDICPAKS, owner, content)

        # Behaviour to handle a Call For Backup request
        template = Template()
        template.set_metadata("performative", "cfm")
        self.add_behaviour(CallForMedicResponderBehaviour(), template)

    """
    Decides if agent accepts the CFM request
    
    This method is a decision function invoked when a CALL FOR MEDIC request has arrived.
    Parameter <tt> sContent</tt> is the content of message received in <tt> CFM</tt> responder behaviour as
    result of a <tt> CallForMedic</tt> request, so it must be: <tt> ( x , y , z ) ( health ) </tt>.
    By default, the return value is <tt> TRUE</tt>, so agents always accept all CFM requests.
    
    <em> It's very useful to overload this method. </em>
    
    @param _sContent
    @return <tt> TRUE</tt>
    """

    def check_medic_action(self, _sContent):
        # We always go to help (we are like Mother Teresa of Calcutta)
        return True

    def perform_medic_action(self):
        # We can give medic paks if we have power enough...
        if self.get_power() >= 25:
            self.use_power()
            return True

        return False

    """
    Action to do when this agent reaches the target of current task.
    
    This method is called when this agent goes to state <em>TARGET_REACHED</em>. If current task is <tt> TASK_GIVE_MEDICPAKS</tt>,
    agent must give medic packs, but in other case, it calls to parent's method.
    
    <em> It's very useful to overload this method. </em>
    
    @param _CurrentTask
    """

    def perform_target_reached(self, current_task):
        if current_task.type == TASK_NONE:
            pass
        elif current_task.type == TASK_GIVE_MEDICPAKS:
            packs_delivered = self.create_medic_pack()
            current_task.packs_delivered += packs_delivered
        else:
            super().perform_target_reached(current_task)

    """
    Creates medic packs if possible.
    
    This method allows to create medic packs if there is enough power in the agent's power bar.
    
    @return iPacksDelivered: number of medic packs created
    """

    def create_medic_pack(self):
        packs_delivered = 0
        while self.perform_medic_action():
            Medic.packs_delivered += 1
            name = "medicpack" + str(Medic.packs_delivered) + "@" + self.name.split('@')[1]

            x = self.movement.position.x / 8
            z = self.movement.position.z / 8
            team = self.team

            try:
                agent = MedicPack(name=name, passwd="secret", x=x, z=z, team=team, manager_jid=self.manager)
                agent.start()
            except:
                logger.info("Medic " + str(self.name) + ": Could not create MedicPack")

            # time.sleep(0.5)
            packs_delivered += 1

        return packs_delivered
