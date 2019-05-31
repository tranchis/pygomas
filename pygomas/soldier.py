import json

from spade.behaviour import CyclicBehaviour
from spade.template import Template

from .agent import LONG_RECEIVE_WAIT
from .bditroop import BDITroop, CLASS_SOLDIER
from .ontology import BACKUP_SERVICE, PERFORMATIVE, PERFORMATIVE_CFB
from .task import TASK_NONE, TASK_GIVE_MEDICPAKS, TASK_GIVE_AMMOPACKS, TASK_GIVE_BACKUP, TASK_GET_OBJECTIVE, \
    TASK_ATTACK, TASK_RUN_AWAY, TASK_GOTO_POSITION, TASK_PATROLLING, TASK_WALKING_PATH, TASK_RETURN_TO_BASE


class Soldier(BDITroop):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.services.append(BACKUP_SERVICE)
        self.eclass = CLASS_SOLDIER

    async def setup(self):
        self.launch_cfb_responder_behaviour()

    def setup_priorities(self):

        self.task_manager.set_priority(TASK_NONE, 0)
        self.task_manager.set_priority(TASK_GIVE_MEDICPAKS, 0)
        self.task_manager.set_priority(TASK_GIVE_AMMOPACKS, 0)
        self.task_manager.set_priority(TASK_GIVE_BACKUP, 1000)
        self.task_manager.set_priority(TASK_GET_OBJECTIVE, 2000)
        self.task_manager.set_priority(TASK_ATTACK, 1000)
        self.task_manager.set_priority(TASK_RUN_AWAY, 1500)
        self.task_manager.set_priority(TASK_GOTO_POSITION, 750)
        self.task_manager.set_priority(TASK_PATROLLING, 500)
        self.task_manager.set_priority(TASK_WALKING_PATH, 750)
        self.task_manager.set_priority(TASK_RETURN_TO_BASE, 2001)

    # Behaviours to handle calls for services we offer

    # Call For Backup
    def launch_cfb_responder_behaviour(self):
        class CallForBackupResponderBehaviour(CyclicBehaviour):
            async def run(self):
                msg = await self.receive(timeout=LONG_RECEIVE_WAIT)
                if msg:
                    owner = msg.sender
                    content = json.loads(msg.body)

                    if self.agent.check_backup_action(content):
                        self.agent.task_manager.add_task(
                            TASK_GIVE_BACKUP, owner, content)

        # Behaviour to handle a Call For Backup request

        template = Template()
        template.set_metadata(PERFORMATIVE, PERFORMATIVE_CFB)
        self.add_behaviour(CallForBackupResponderBehaviour(), template)

    def check_backup_action(self, content):
        """
        Decides if agent accepts the CFB request

        This method is a decision function invoked when a CALL FOR BACKUP request has arrived.
        Parameter content is the content of message received in CFB responder behaviour as
        result of a CallForBackup request, so it must be: ( x , y , z ) ( SoldiersCount ).
        By default, the return value is True, so agents always accepts all CFB requests.

        It's very useful to overload this method.

        :param content
        :returns True
        """
        # We always go to help (we are like Mother Teresa of Calcutta again)
        return True

    def perform_backup_action(self):
        # Do we need to inform to that agent?
        return True
