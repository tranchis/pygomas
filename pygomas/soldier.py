from spade.behaviour import CyclicBehaviour
from spade.template import Template
from .troop import Troop, CLASS_SOLDIER
from pygomas.ontology import BACKUP_SERVICE
from .task import TASK_NONE, TASK_GIVE_MEDICPAKS, TASK_GIVE_AMMOPACKS, TASK_GIVE_BACKUP, TASK_GET_OBJECTIVE, \
    TASK_ATTACK, TASK_RUN_AWAY, TASK_GOTO_POSITION, TASK_PATROLLING, TASK_WALKING_PATH


class Soldier(Troop):
    """
    'setup' method of jade agents.

    This method perform actions in common to CSoldier agents (and derived classes)
    and calls parent's setup.
    """

    async def setup(self):
        self.services.append(BACKUP_SERVICE)
        self.eclass = CLASS_SOLDIER
        self.launch_cfb_responder_behaviour()

    def setup_priorities(self):

        self.task_priority[TASK_NONE] = 0
        self.task_priority[TASK_GIVE_MEDICPAKS] = 0
        self.task_priority[TASK_GIVE_AMMOPACKS] = 0
        self.task_priority[TASK_GIVE_BACKUP] = 1000
        self.task_priority[TASK_GET_OBJECTIVE] = 2000
        self.task_priority[TASK_ATTACK] = 1000
        self.task_priority[TASK_RUN_AWAY] = 1500
        self.task_priority[TASK_GOTO_POSITION] = 750
        self.task_priority[TASK_PATROLLING] = 500
        self.task_priority[TASK_WALKING_PATH] = 750

    # Behaviours to handle calls for services we offer

    # Call For Backup
    def launch_cfb_responder_behaviour(self):
        class CallForBackupResponderBehaviour(CyclicBehaviour):
            async def run(self):
                msg = await self.receive(timeout=100000)
                if msg:
                    owner = msg.sender
                    content = msg.body

                    if self.agent.check_backup_action(content):
                        self.agent.add_task(TASK_GIVE_BACKUP, owner, content)

        # Behaviour to handle a Call For Backup request

        template = Template()
        template.set_metadata("performative", "cfb")
        self.add_behaviour(CallForBackupResponderBehaviour(), template)

    '''/**
     * Decides if agent accepts the CFB request
     *
     * This method is a decision function invoked when a CALL FOR BACKUP request has arrived.
     * Parameter <tt> sContent</tt> is the content of message received in <tt> CFB</tt> responder behaviour as
     * result of a <tt> CallForBackup</tt> request, so it must be: <tt> ( x , y , z ) ( SoldiersCount ) </tt>.
     * By default, the return value is <tt> TRUE</tt>, so agents always accepts all CFB requests.
     *
     * <em> It's very useful to overload this method. </em>
     *
     * @param _sContent
     * @return <tt> TRUE</tt>
     *
     */'''

    def check_backup_action(self, content):
        # We always go to help (we are like Mother Teresa of Calcutta again)
        return True

    # /////////////////////////////////////////////////////////////////////////////////////////////////////

    # /////////////////////////////////////////////////////////////////////////////////////////////////////
    def perform_backup_action(self):
        # Do we need to inform to that agent?
        return True
    # /////////////////////////////////////////////////////////////////////////////////////////////////////
