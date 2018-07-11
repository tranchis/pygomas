from spade.template import Template
from spade.behaviour import Behaviour
from jgomas.CAmmoPack import CAmmoPack
from jgomas.CTask import CTask
from jgomas.CTroop import CTroop

import time

class CFieldOps(CTroop):

    '''/**
     * inner variable used to name packs
     */'''
    m_iPacksDelivered = 0

    '''/**
     * 'setup' method of SPADE agents.
     *
     * This method perform actions in common to CFieldOps agents (and derived classes)
     * and calls parent's setup.
     *
     */'''
    def start(self, auto_register=True):
        self.m_ServiceList.append(CTroop.AMMO_SERVICE)
        self.m_eClass = self.CLASS_FIELDOPS
        CTroop.start(self, auto_register=auto_register)
        self.Launch_CFA_ResponderBehaviour()

    def SetUpPriorities(self):

        self.m_TaskPriority[CTask.TASK_NONE] = 0
        self.m_TaskPriority[CTask.TASK_GIVE_MEDICPAKS] = 0
        self.m_TaskPriority[CTask.TASK_GIVE_AMMOPACKS] = 2000
        self.m_TaskPriority[CTask.TASK_GIVE_BACKUP] = 0
        self.m_TaskPriority[CTask.TASK_GET_OBJECTIVE] = 1000
        self.m_TaskPriority[CTask.TASK_ATTACK] = 1000
        self.m_TaskPriority[CTask.TASK_RUN_AWAY] = 1500
        self.m_TaskPriority[CTask.TASK_GOTO_POSITION] = 750
        self.m_TaskPriority[CTask.TASK_PATROLLING] = 500
        self.m_TaskPriority[CTask.TASK_WALKING_PATH] = 750

    # Behaviours to handle calls for services we offer

    # Call For Ammo
    def Launch_CFA_ResponderBehaviour(self):
        class CyclicBehaviour(Behaviour):
            async def run(self):
                msgCFB = await self.receive(timeout=100000)
                if msgCFB:
                    owner = msgCFB.sender
                    sContent = msgCFB.body

                    if self.agent.checkBackupAction(sContent):
                        self.agent.AddTask(CTask.TASK_GIVE_AMMOPACKS, owner, sContent)

        # Behaviour to handle a Call For Backup request
        template = Template()
        template.set_metadata("performative", "cfa")
        self.add_behaviour(CyclicBehaviour(), template)

    '''/**
     * Decides if agent accepts the CFA request
     *
     * This method is a decision function invoked when a CALL FOR AMMO request has arrived.
     * Parameter <tt> sContent</tt> is the content of message received in <tt> CFA</tt> responder behaviour as
     * result of a <tt> CallForAmmo</tt> request, so it must be: <tt> ( x , y , z ) ( ammo ) </tt>.
     * By default, the return value is <tt> TRUE</tt>, so agents always accept all CFA requests.
     *
     * <em> It's very useful to overload this method. </em>
     *
     * @param _sContent
     * @return <tt> TRUE</tt>
     *
     */'''
    def checkAmmoAction(self, _sContent):
        ## We always go to help (we are like Mother Teresa of Calcutta)
        return True
    #/////////////////////////////////////////////////////////////////////////////////////////////////////

    #/////////////////////////////////////////////////////////////////////////////////////////////////////
    def performAmmoAction(self):
        ## We can give ammo paks if we have power enough...
        if self.GetPower() >= 25:
            self.UsePower()
            return True
        return False
    #/////////////////////////////////////////////////////////////////////////////////////////////////////

    #/////////////////////////////////////////////////////////////////////////////////////////////////////
    '''/**
     * Action to do when this agent reaches the target of current task.
     *
     * This method is called when this agent goes to state <em>TARGET_REACHED</em>. If current task is <tt> TASK_GIVE_AMMOPACKS</tt>,
     * agent must give ammo packs, but in other case, it calls to parent's method.
     *
     * <em> It's very useful to overload this method. </em>
     *
     * @param _CurrentTask
     *
     */'''
    def PerformTargetReached(self, _CurrentTask):

        if _CurrentTask.m_iType == CTask.TASK_NONE:
            pass

        elif _CurrentTask.m_iType == CTask.TASK_GIVE_AMMOPACKS:
            iPacksDelivered = 0
            iPacksDelivered = self.CreateAmmoPack()
            _CurrentTask.m_iPacksDelivered += iPacksDelivered

        else:
            CTroop.PerformTargetReached(self,_CurrentTask)
    #/////////////////////////////////////////////////////////////////////////////////////////////////////

    #/////////////////////////////////////////////////////////////////////////////////////////////////////
    '''/**
     * Creates ammo packs if possible.
     *
     * This method allows to create medic packs if there is enough power in the agent's power bar.
     *
     * @return iPacksDelivered: number of ammo packs created
     *
     */'''
    def CreateAmmoPack(self):

        iPacksDelivered = 0
        sName = ""
        while self.performAmmoAction():
            ## if we give ammo paks, need inform to that agent?
            CFieldOps.m_iPacksDelivered += 1
            sName = "ammopack" + str(CFieldOps.m_iPacksDelivered) + "@" + self.getDomain()
            x = self.m_Movement.m_Position.x / 8
            z = self.m_Movement.m_Position.z / 8
            eTeam = self.m_eTeam

            aController = CAmmoPack(sName, "secret", x,z,eTeam)
            aController.start()

            time.sleep(0.5)
            iPacksDelivered +=  1
            print ("AmmoPack created!!")

        return iPacksDelivered
