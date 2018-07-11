import time

from jgomas.CTroop import CTroop
from jgomas.CTask import CTask
from jgomas.CMedicPack import CMedicPack
from spade.template import Template
from spade.behaviour import Behaviour

class CMedic(CTroop):
    m_iPacksDelivered = 0
    """
    'setup' method of spade agents.
    
    This method perform actions in common to CMedic agents (and derived classes)
    and calls parent's setup.
    """
    def start(self, auto_register=True):
        self.m_ServiceList.append(CTroop.MEDIC_SERVICE)
        self.m_eClass = self.CLASS_MEDIC
        CTroop.start(self, auto_register=auto_register)
        self.Launch_CFM_ResponderBehaviour()

    def SetUpPriorities(self):
        self.m_TaskPriority[CTask.TASK_NONE] = 0
        self.m_TaskPriority[CTask.TASK_GIVE_MEDICPAKS] = 2000
        self.m_TaskPriority[CTask.TASK_GIVE_AMMOPACKS] = 0
        self.m_TaskPriority[CTask.TASK_GIVE_BACKUP] = 0
        self.m_TaskPriority[CTask.TASK_GET_OBJECTIVE] = 1000
        self.m_TaskPriority[CTask.TASK_ATTACK] = 1000
        self.m_TaskPriority[CTask.TASK_RUN_AWAY] = 1500
        self.m_TaskPriority[CTask.TASK_GOTO_POSITION] = 750
        self.m_TaskPriority[CTask.TASK_PATROLLING] = 500
        self.m_TaskPriority[CTask.TASK_WALKING_PATH] = 750


    # Behaviours to handle calls for services we offer

    # Call For Medic
    def Launch_CFM_ResponderBehaviour(self):
        class CyclicBehaviour(Behaviour):
            async def run(self):
                msgCFB = await self.receive(timeout=100000)
                if msgCFB:
                    owner = msgCFB.sender
                    sContent = msgCFB.body

                    if self.agent.checkBackupAction(sContent):
                        self.agent.AddTask(CTask.TASK_GIVE_MEDICPAKS, owner, sContent)

        # Behaviour to handle a Call For Backup request
        template = Template()
        template.set_metadata("performative", "cfm")
        self.add_behaviour(CyclicBehaviour(), template)

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
    def checkMedicAction(self, _sContent):
        # We always go to help (we are like Mother Teresa of Calcutta)
        return True

    def performMedicAction(self):
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
    def PerformTargetReached(self, _CurrentTask):
        if _CurrentTask.m_iType == CTask.TASK_NONE:
            pass
        elif _CurrentTask.m_iType == CTask.TASK_GIVE_MEDICPAKS:
            iPacksDelivered = 0
            iPacksDelivered = self.CreateMedicPack()
            _CurrentTask.m_iPacksDelivered += iPacksDelivered
        else:
            CTroop.PerformTargetReached(self,_CurrentTask)

    """
    Creates medic packs if possible.
    
    This method allows to create medic packs if there is enough power in the agent's power bar.
    
    @return iPacksDelivered: number of medic packs created
    """
    def CreateMedicPack(self):
        iPacksDelivered = 0
        sName = ""
        while self.performMedicAction():
            CMedic.m_iPacksDelivered += 1
            sName = "medicpack" + str(CMedic.m_iPacksDelivered) + "@" + self.name.split('@')[1]

            x = self.m_Movement.m_Position.x / 8
            z = self.m_Movement.m_Position.z / 8
            team = self.m_eTeam

            try:
                agent = CMedicPack(sName, "secret", x, z, team)
                agent.start()
            except:
                print("Medic "+str(self.name)+": Could not create MedicPack")

            time.sleep(0.5)
            iPacksDelivered += 1

        return iPacksDelivered
