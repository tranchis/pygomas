from jgomas.CTroop import CTroop
from jgomas.CTask import CTask
from spade.behaviour import Behaviour
from spade.template import Template


class CSoldier(CTroop):

    '''
    'setup' method of jade agents.

    This method perform actions in common to CSoldier agents (and derived classes)
    and calls parent's setup.
    '''
    def start(self, auto_register=True):

        self.m_ServiceList.append(CTroop.BACKUP_SERVICE)
        self.m_eClass = self.CLASS_SOLDIER
        CTroop.start(self, auto_register=auto_register)
        self.Launch_CFB_ResponderBehaviour()

    def SetUpPriorities(self):

        self.m_TaskPriority[CTask.TASK_NONE] = 0
        self.m_TaskPriority[CTask.TASK_GIVE_MEDICPAKS] = 0
        self.m_TaskPriority[CTask.TASK_GIVE_AMMOPACKS] = 0
        self.m_TaskPriority[CTask.TASK_GIVE_BACKUP] = 1000
        self.m_TaskPriority[CTask.TASK_GET_OBJECTIVE] = 2000
        self.m_TaskPriority[CTask.TASK_ATTACK] = 1000
        self.m_TaskPriority[CTask.TASK_RUN_AWAY] = 1500
        self.m_TaskPriority[CTask.TASK_GOTO_POSITION] = 750
        self.m_TaskPriority[CTask.TASK_PATROLLING] = 500
        self.m_TaskPriority[CTask.TASK_WALKING_PATH] = 750

    # Behaviours to handle calls for services we offer

    # Call For Backup
    def Launch_CFB_ResponderBehaviour(self):
        class CyclicBehaviour(Behaviour):
            async def run(self):
                msgCFB = await self.receive(timeout=100000)
                if msgCFB:
                    owner = msgCFB.sender
                    sContent = msgCFB.body

                    if self.agent.checkBackupAction(sContent):
                        self.agent.AddTask(CTask.TASK_GIVE_BACKUP, owner, sContent)

        # Behaviour to handle a Call For Backup request

        template = Template()
        template.set_metadata("performative", "cfb")
        self.add_behaviour(CyclicBehaviour(), template)

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
    def checkBackupAction(self, _sContent):
        ## We always go to help (we are like Mother Teresa of Calcutta again)
        return True
    #/////////////////////////////////////////////////////////////////////////////////////////////////////

    #/////////////////////////////////////////////////////////////////////////////////////////////////////
    def performBackupAction(self):
        ## Do we need to inform to that agent?
        return True
    #/////////////////////////////////////////////////////////////////////////////////////////////////////