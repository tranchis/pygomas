from jgomas.CMobile import CMobile
from jgomas.Vector3D import Vector3D
from jgomas.CPack import CPack
from jgomas.CJGomasAgent import CJGomasAgent
from jgomas.CConfig import CConfig
from jgomas.CService import CService
from spade.behaviour import OneShotBehaviour, PeriodicBehaviour, Behaviour, TimeoutBehaviour
from jgomas.CServer import CServer
from spade.template import Template
from jgomas.CTroop import CTroop
from spade.message import Message
from jgomas.CObjPack import CObjPack
from jgomas.CTerrainMap import CTerrainMap
from jgomas.CSight import CSight
import time
import math


class CPackStatistic:

    def __init__(self):
        self.m_iDelivered = 0
        self.m_iTeamTaken = 0
        self.m_iEnemyTaken = 0
        self.m_iNotTaken = 0

    def __str__(self):
        ret = "\t\t* Delivered:   \t" + str(self.m_iDelivered)+"\n"
        ret += "\t\t* Team Taken:  \t" + str(self.m_iTeamTaken)+"\n"
        ret += "\t\t* Enemy Taken: \t" + str(self.m_iEnemyTaken)+"\n"
        ret += "\t\t* Not Taken:   \t" + str(self.m_iNotTaken)+"\n"
        return ret


class CTeamStatistic:

    PACK_MEDICPACK = 0
    PACK_AMMOPACK = 1

    def __init__(self):

        self.m_iPacks = {
            self.PACK_MEDICPACK: CPackStatistic(),
            self.PACK_AMMOPACK: CPackStatistic()
        }

        self.m_iTotalShots = 0
        self.m_iEnemyHitShots = 0
        self.m_iTeamHitShots = 0
        self.m_iFailedShots = 0

        self.m_iTotalObjectiveTaken = 0
        self.m_iTotalObjectiveLost = 0

        self.m_dMedicEfficiency = 0
        self.m_dFieldOpsEfficiency = 0
        self.m_dArmyEfficiency = 0

        self.m_iAlivePlayers = 0
        self.m_fAverageHealth = 0

    def CalculateEfficiency(self, _AliveEnemies):

        if self.m_iPacks[self.PACK_MEDICPACK].m_iDelivered <= 0:
            self.m_dMedicEfficiency = 0
        else:
            not_taken = self.m_iPacks[self.PACK_MEDICPACK].m_iNotTaken
            delivered = self.m_iPacks[self.PACK_MEDICPACK].m_iDelivered
            self.m_dMedicEfficiency = 1.0 - (not_taken * 1.0) / delivered

        if self.m_iPacks[self.PACK_AMMOPACK].m_iDelivered <= 0:
            self.m_dFieldOpsEfficiency = 0
        else:
            not_taken = self.m_iPacks[self.PACK_AMMOPACK].m_iNotTaken
            delivered = self.m_iPacks[self.PACK_AMMOPACK].m_iDelivered
            self.m_dFieldOpsEfficiency = 1.0 - (not_taken * 1.0) / delivered

        if self.m_iTotalShots <= 0:
            self.m_dArmyEfficiency = 0
        else:
            self.m_dArmyEfficiency = 1.0 - (_AliveEnemies * 1.0) / self.m_iTotalShots

    def CalculateAntiEfficiency(self):

        if self.m_iPacks[self.PACK_MEDICPACK].m_iDelivered <= 0:
            self.m_dMedicAntiEfficiency = 0
        else:
            enemy_taken = self.m_iPacks[self.PACK_MEDICPACK].m_iEnemyTaken
            delivered = self.m_iPacks[self.PACK_MEDICPACK].m_iDelivered
            self.m_dMedicAntiEfficiency = (enemy_taken * 1.0) / delivered

        if self.m_iPacks[self.PACK_AMMOPACK].m_iDelivered <= 0:
            self.m_dFieldOpsAntiEfficiency = 0
        else:
            enemy_taken = self.m_iPacks[self.PACK_AMMOPACK].m_iEnemyTaken
            delivered = self.m_iPacks[self.PACK_AMMOPACK].m_iDelivered
            self.m_dFieldOpsAntiEfficiency = (enemy_taken * 1.0) / delivered

        if self.m_iTeamHitShots <= 0:
            self.m_dArmyAntiEfficiency = 0
        else:
            self.m_dArmyAntiEfficiency = (self.m_iAlivePlayers * 1.0) / self.m_iTeamHitShots

    def __str__(self):

        ret = "\t-GENERAL:\n"
        ret += "\t\t* Alive:       \t" + str(self.m_iAlivePlayers)+"\n"
        ret += "\t\t* Avrg. Health:\t" + str(self.m_fAverageHealth)+"\n"

        ret += "\t-OBJECTIVE:\n"
        ret += "\t\t* Times Taken: \t" + str(self.m_iTotalObjectiveTaken)+"\n"
        ret += "\t\t* Times Lost:  \t" + str(self.m_iTotalObjectiveLost)+"\n"

        ret += "\t-SHOTS:\n"
        ret += "\t\t* EnemyHit:    \t" + str(self.m_iEnemyHitShots)+"\n"
        ret += "\t\t* TeamHit:     \t" + str(self.m_iTeamHitShots)+"\n"
        ret += "\t\t* FailedHit:   \t" + str(self.m_iFailedShots)+"\n"
        ret += "\t\t* TOTAL:       \t" + str(self.m_iTotalShots)+"\n"

        ret += "\t-MEDIC PACKS:\n"
        ret += str(self.m_iPacks[self.PACK_MEDICPACK])+"\n"

        ret += "\t-AMMO PACKS:\n"
        ret += str(self.m_iPacks[self.PACK_AMMOPACK])+"\n"

        ret += "\t-EFICIENCY:\n"
        ret += "\t\t* Medic:       \t" + str(self.m_dMedicEfficiency)+"\n"
        ret += "\t\t* FieldOps:    \t" + str(self.m_dFieldOpsEfficiency)+"\n"
        ret += "\t\t* Army:        \t" + str(self.m_dArmyEfficiency)+"\n"

        ret += "\t-ANTI-EFICIENCY:"+"\n"
        ret += "\t\t* Medic:       \t" + str(self.m_dMedicAntiEfficiency)+"\n"
        ret += "\t\t* FieldOps:    \t" + str(self.m_dFieldOpsAntiEfficiency)+"\n"
        ret += "\t\t* Army:        \t" + str(self.m_dArmyAntiEfficiency)+"\n"

        return ret


class CGameStatistic:

    TEAM_ALLIED = 0
    TEAM_AXIS = 1

    def __init__(self):
        self.m_tTeamStatistic = {
            self.TEAM_ALLIED: CTeamStatistic(),
            self.TEAM_AXIS: CTeamStatistic()
        }

        self.m_lMatchDuration = 0

    def CalculateData(self,
                      _iAlliedAlivePlayers,
                      _iAxisAlivePlayers,
                      _iAlliedHealth,
                      _iAxisHealth):

        self.m_tTeamStatistic[self.TEAM_ALLIED].m_iAlivePlayers = _iAlliedAlivePlayers
        if _iAlliedAlivePlayers > 0:
            self.m_tTeamStatistic[self.TEAM_ALLIED].m_fAverageHealth = \
                (_iAlliedHealth * 1.0) / _iAlliedAlivePlayers
        else:
            self.m_tTeamStatistic[self.TEAM_ALLIED].m_fAverageHealth = 0

        self.m_tTeamStatistic[self.TEAM_AXIS].m_iAlivePlayers = _iAxisAlivePlayers
        if _iAxisAlivePlayers > 0:
            self.m_tTeamStatistic[self.TEAM_AXIS].m_fAverageHealth = \
                (_iAxisHealth * 1.0) / _iAxisAlivePlayers
        else:
            self.m_tTeamStatistic[self.TEAM_AXIS].m_fAverageHealth = 0

        self.m_tTeamStatistic[self.TEAM_ALLIED].CalculateEfficiency(_iAxisAlivePlayers)
        self.m_tTeamStatistic[self.TEAM_ALLIED].CalculateAntiEfficiency()

        self.m_tTeamStatistic[self.TEAM_AXIS].CalculateEfficiency(_iAlliedAlivePlayers)
        self.m_tTeamStatistic[self.TEAM_AXIS].CalculateAntiEfficiency()

    def __str__(self, _sWinnerTeam=""):

        self.m_lMatchDuration = self.m_lMatchDuration / 1000
        iHours = int(self.m_lMatchDuration / 3600)
        iMinutes = int((self.m_lMatchDuration % 3600) / 60)
        iSeconds = int((self.m_lMatchDuration -
                        ((iHours * 3600) + (iMinutes * 60))))

        ret = "Winner Team: " + _sWinnerTeam + "\n"
        if iHours <= 0:
            ret += "Duration: [" + \
                   str(iMinutes) + "m:" + \
                   str(iSeconds) + "s]\n"
        else:
            ret += "Duration: [" + \
                   str(iHours) + "h:" + \
                   str(iMinutes) + "m:" + \
                   str(iSeconds) + "s]\n"

        ret += "Statistics for ALLIED TEAM\n"
        ret += str(self.m_tTeamStatistic[self.TEAM_ALLIED])

        ret += "\n"
        ret += "Statistics for AXIS TEAM\n"
        ret += str(self.m_tTeamStatistic[self.TEAM_AXIS])

        ret = ret+"\n"
        return ret


class CMicroAgent:

    def __init__(self, ):
        self.m_JID = ""
        self.m_eTeam = 0
        self.m_Locate = CMobile()
        self.m_bCarryingObjective = False
        self.m_bShooting = False
        self.m_iHealth = 0
        self.m_iAmmo = 0
        self.m_eType = 0


class CDinObject:

    m_Index = 0

    def __str__(self):
        return "DO(" + str(CPack.pack_name[self.m_eType]) + "," + \
               str(self.m_Position) + ")"

    def __init__(self):
        self.m_Position = Vector3D()
        self.m_eType = CPack.PACK_NONE
        self.m_eTeam = 0
        self.m_bTaken = False
        self.m_Owner = 0
        CDinObject.m_Index += 1
        self.m_id = CDinObject.m_Index


class CManager(CJGomasAgent):

    ARG_PLAYERS = 0
    ARG_MAP_NAME = 1
    ARG_FPS = 2
    ARG_MATCH_TIME = 3
    ARG_MAP_PATH = 4

    def __init__(self,
                 name="cmanager@localhost",
                 passwd="secret",
                 players=10,
                 fps=0.033,
                 match_time=380,
                 path=None,
                 mapname="map_01",
                 service_jid="cservice@localhost"):

        CJGomasAgent.__init__(self, name, passwd, service_jid=service_jid)
        self.MAX_TOTAL_AGENTS = players
        self.m_iFPS = fps
        self.m_lMatchTime = match_time
        self.m_sMapName = str(mapname)
        self.m_CConfig = CConfig()
        if path is not None:
            self.m_CConfig.setDataPath(path)
        self.m_iNumberOfAgents = 0
        self.m_AgentList = {}
        self.m_lMatchInit = 0
        self.m_domain = name.split('@')[1]
        self.ObjectiveAgent = None
        self.cservice = None

        # self.addAddress("http://"+self.getDomain()+":2099/acc")


    def take_down(self):
        self.ObjectiveAgent.stop()
        CJGomasAgent.take_down(self)

    def start(self, auto_register=True):
        class InitBehaviour(OneShotBehaviour):
            async def run(self):
                print("Manager (Expected Agents): " + str(self.agent.MAX_TOTAL_AGENTS))

                for i in range(1, self.agent.MAX_TOTAL_AGENTS + 1):
                    msg = await self.receive(timeout=100000)
                    if msg:
                        sContent = msg.body
                        tokens = sContent.lower().split()

                        sName = None
                        eType = None
                        eTeam = None

                        for token in tokens:
                            if token == "name:":
                                sName = tokens[tokens.index(token) + 1]
                            elif token == "type:":
                                eType = int(tokens[tokens.index(token) + 1])
                            elif token == "team:":
                                eTeam = int(tokens[tokens.index(token) + 1])

                        self.agent.m_AgentList[sName] = CMicroAgent()

                        self.agent.m_AgentList[sName].m_JID = sName
                        self.agent.m_AgentList[sName].m_eType = eType
                        self.agent.m_AgentList[sName].m_eTeam = eTeam

                        print("Manager: [" + sName + "] is Ready!")
                        self.agent.m_iNumberOfAgents += 1

                print("Manager (Accepted Agents): " + str(self.agent.m_iNumberOfAgents))
                for agent in self.agent.m_AgentList.values():
                    msg = Message()
                    msg.set_metadata("performative", "init")
                    msg.to = agent.m_JID
                    msg.body = " MAP: " + self.agent.m_sMapName + " FIGHT!!"
                    await self.send(msg)
                    print("Manager: Sending notification to fight to: " + agent.m_JID)

                await self.agent.InformObjectives(self)
                self.agent.m_lMatchInit = time.time()

        print("JGOMAS v. 0.1.4 (c) GTI-IA 2005 - 2007 (DSIC / UPV)")
        CJGomasAgent.start(self, auto_register=auto_register)

        self.m_GameStatistic = CGameStatistic()

        # Manager notify its services in a different way
        self.cservice = CService(self.service_jid)
        self.cservice.start()



        self.register_service("management")

        self.m_DinObjectList = dict()
        self.m_REServer = CServer(self.m_sMapName)
        self.m_REServer.start()

        self.m_Map = CTerrainMap()
        self.m_Map.LoadMap(self.m_sMapName, self.m_CConfig)

        self.CreateObjectives()  # We need to do this when online

        #// Behaviour to refresh all render engines connected
        self.Launch_RenderEngine_InformBehaviour()

        # Behaviour to listen to data (position, health?, an so on) from troop agents
        self.Launch_DataFromTroop_ListenerBehaviour()

        # Behaviour to handle Sight messages
        self.Launch_Sight_ResponderBehaviour()

        # Behaviour to handle Shot messages
        self.Launch_Shot_ResponderBehaviour()

        # Behaviour to attend the petitions for register services
        self.Launch_ServiceRegister_ResponderBehaviour()

        # Behaviour to handle Pack Management: Creation and Destruction
        self.Launch_PackManagement_ResponderBehaviour()

        # Behaviour to inform all agents that game has finished by time
        self.Launch_GameTimeout_InformBehaviour()

        template = Template()
        template.set_metadata("performative", "init")
        self.add_behaviour(InitBehaviour(), template)

    # Behaviour to refresh all render engines connected
    def Launch_RenderEngine_InformBehaviour(self):

        class TickerBehaviour(PeriodicBehaviour):
            async def run(self):
                try:
                    if self.agent.m_REServer and self.agent.m_REServer.m_ConnectionList is not None:

                        msg = "" + str(self.agent.m_iNumberOfAgents) + " "
                        for agent in self.agent.m_AgentList.values():
                            msg += agent.m_sName.split("@")[0] + " "
                            msg += str(agent.m_eType) + " "
                            msg += str(agent.m_eTeam) + " "

                            msg += str(agent.m_iHealth) + " "
                            msg += str(agent.m_iAmmo) + " "
                            if agent.m_bCarryingObjective:
                                msg += str(1)
                            else:
                                msg += str(0)

                            msg += " (" + str(agent.m_Locate.m_Position.x) + ", "
                            msg += str(agent.m_Locate.m_Position.y) + ", "
                            msg += str(agent.m_Locate.m_Position.z) + ") "

                            msg += "(" + str(agent.m_Locate.m_Velocity.x) + ", "
                            msg += str(agent.m_Locate.m_Velocity.y) + ", "
                            msg += str(agent.m_Locate.m_Velocity.z) + ") "

                            msg += "(" + str(agent.m_Locate.m_Heading.x) + ", "
                            msg += str(agent.m_Locate.m_Heading.y) + ", "
                            msg += str(agent.m_Locate.m_Heading.z) + ") "

                        msg += str(len(self.agent.m_DinObjectList)) + " "

                        for oDinObject in self.agent.m_DinObjectList.values():
                            msg += str(oDinObject.m_id) + " "
                            msg += str(oDinObject.m_eType) + " "
                            msg += " (" + str(oDinObject.m_Position.x) + ", "
                            msg += str(oDinObject.m_Position.y) + ", "
                            msg += str(oDinObject.m_Position.z) + ") "

                        for st in self.agent.m_REServer.m_ConnectionList:
                            st.SendMsgToRenderEngine(CServer.CRequestHandler.TCP_AGL, msg)
                except:
                    pass

        self.add_behaviour(TickerBehaviour(self.m_iFPS))

    # Behaviour to listen to data (position, health?, an so on) from troop agents
    def Launch_DataFromTroop_ListenerBehaviour(self):
        class CyclicBehaviourDFT(Behaviour):
            async def run(self):
                msg = await self.receive(timeout=100000)
                if msg:
                    s_content = msg.body
                    s_content = s_content.split()
                    id_agent = int(s_content[1])
                    self.agent.m_AgentList[id_agent].m_Locate.m_Position.x = float(s_content[3])
                    self.agent.m_AgentList[id_agent].m_Locate.m_Position.y = float(s_content[5])
                    self.agent.m_AgentList[id_agent].m_Locate.m_Position.z = float(s_content[7])

                    self.agent.m_AgentList[id_agent].m_Locate.m_Velocity.x = float(s_content[10])
                    self.agent.m_AgentList[id_agent].m_Locate.m_Velocity.y = float(s_content[12])
                    self.agent.m_AgentList[id_agent].m_Locate.m_Velocity.z = float(s_content[14])

                    self.agent.m_AgentList[id_agent].m_Locate.m_Heading.x = float(s_content[17])
                    self.agent.m_AgentList[id_agent].m_Locate.m_Heading.y = float(s_content[19])
                    self.agent.m_AgentList[id_agent].m_Locate.m_Heading.z = float(s_content[21])

                    self.agent.m_AgentList[id_agent].m_iHealth = int(s_content[24])
                    self.agent.m_AgentList[id_agent].m_iAmmo = int(s_content[26])

                    self.agent.CheckObjectsAtStep(id_agent)
                    if self.agent.CheckGameFinished(id_agent):
                        self.agent.InformGameFinished("ALLIED", self)
                        print("\n\nManager:  GAME FINISHED!! Winner Team: ALLIED! (Target Returned)\n")

        template = Template()
        template.set_metadata("performative", "data")

        self.add_behaviour(CyclicBehaviourDFT(), template)

    # Behaviour to handle Sight messages
    def Launch_Sight_ResponderBehaviour(self):

        class CyclicBehaviourSight(Behaviour):

            async def run(self):
                msg = await self.receive(timeout=100000)
                if msg:
                    s_content = msg.body
                    s_content = s_content.split()

                    FOVObjects = self.agent.GetObjectsInFieldOfView(s_content[1])

                    s_content = " #: " + str(len(FOVObjects)) + " "

                    for s in FOVObjects:
                        s_content += "TEAM: " + str(s.m_eTeam) + " TYPE: " + str(s.m_eType)
                        s_content += " ANGLE: " + str(s.m_dAngle) + " DISTANCE: " + str(s.m_dDistance) + " "
                        s_content += "HEALTH: " + str(s.m_iHealth)
                        s_content += " ( " + str(s.m_Position.x) + " , " + str(s.m_Position.y) + " , " + str(s.m_Position.z) + " ) "
                    reply = msg.make_reply()
                    reply.body = s_content
                    reply.set_metadata("performative", "sight")
                    await self.send(reply)

        template = Template()
        template.set_metadata("performative", "sight")
        self.add_behaviour(CyclicBehaviourSight(), template)

    # Behaviour to handle Shot messages
    def Launch_Shot_ResponderBehaviour(self):
        class CyclicBehaviourShot(Behaviour):
            async def run(self):
                msg = await self.receive(True)
                if msg:
                    sContent = msg.body

                    tokens = sContent.split()
                    id = int(tokens[1])
                    iAim = int(tokens[3])
                    iShots = int(tokens[5])

                    iShooterID = 0
                    for agent in self.agent.m_AgentList.values():
                        if agent.m_JID == id:
                            iShooterID = agent.m_JID
                            break
                    if iShooterID == 0:
                        return

                    # Statistics
                    if self.agent.m_AgentList[iShooterID].m_eTeam == CTroop.TEAM_ALLIED:
                        eTeam = 0
                    else:
                        eTeam = 1
                    self.agent.m_GameStatistic.m_tTeamStatistic[eTeam].m_iTotalShots += 1

                    Victim = self.agent.Shot(id)
                    if Victim is None:
                        # Statistics
                        self.agent.m_GameStatistic.m_tTeamStatistic[eTeam].m_iFailedShots += 1
                        return

                    # Statistics
                    if self.agent.m_AgentList[iShooterID].m_eTeam == Victim.m_eTeam:
                        self.agent.m_GameStatistic.m_tTeamStatistic[eTeam].m_iTeamHitShots += 1
                    else:
                        self.agent.m_GameStatistic.m_tTeamStatistic[eTeam].m_iEnemyHitShots += 1

                    iDamage = 2
                    if self.agent.m_AgentList[iShooterID].m_eType == CTroop.CLASS_SOLDIER:
                        iDamage = 3

                    msgShot = Message(to=Victim.m_JID)
                    msgShot.set_metadata("performative", "shot")

                    msgShot.body = "DEC_HEALTH: " + str(iDamage)
                    await self.send(msgShot)

                    self.agent.m_AgentList[Victim.m_JID].m_iHealth -= iDamage
                    if self.agent.m_AgentList[Victim.m_JID].m_iHealth <= 0:
                        self.agent.m_AgentList[Victim.m_JID].m_iHealth = 0
                        print("Agent", str(self.agent.m_AgentList[Victim.m_JID].m_sName), "died")

                        if self.agent.m_AgentList[Victim.m_JID].m_bCarryingObjective == True:
                            self.agent.m_AgentList[Victim.m_JID].m_bCarryingObjective = False
                            print("Agent", str(self.agent.m_AgentList[Victim.m_JID].m_sName), "lost the ObjectivePack")

                            for DinObject in self.agent.m_DinObjectList.values():

                                if DinObject.m_eType == CPack.PACK_OBJPACK:
                                    #Esto sobra: DinObject.m_bTaken = false;
                                    DinObject.m_Owner = 0
                                    msgPack = Message(to=DinObject.m_JID)
                                    msgPack.set_metadata("performative", "pack_lost")
                                    DinObject.m_Position.x = self.agent.m_AgentList[Victim.m_id].m_Locate.m_Position.x
                                    DinObject.m_Position.y = self.agent.m_AgentList[Victim.m_id].m_Locate.m_Position.y
                                    DinObject.m_Position.z = self.agent.m_AgentList[Victim.m_id].m_Locate.m_Position.z
                                    msgPack.body = "POSITION: ( " + \
                                                   str(self.agent.m_AgentList[Victim.m_id].m_Locate.m_Position.x) + \
                                                   " , " + \
                                                   str(self.agent.m_AgentList[Victim.m_id].m_Locate.m_Position.y) + \
                                                   " , " + \
                                                   str(self.agent.m_AgentList[Victim.m_id].m_Locate.m_Position.z) + \
                                                   " ) "
                                    await self.send(msgPack)

                                    # Statistics
                                    self.agent.m_GameStatistic.m_tTeamStatistic[0].m_iTotalObjectiveLost += 1

        template = Template()
        template.set_metadata("performative", "shot")
        self.add_behaviour(CyclicBehaviourShot(), template)

    # Ya no es necesario
    # Behaviour to attend the petitions for register services
    def Launch_ServiceRegister_ResponderBehaviour(self):
        class CyclicBehaviourSR(Behaviour):
            async def run(self):
                msg = await self.receive(timeout=100000)
                if msg:
                    sContent = msg.body
                    Service = self.agent.m_Registry.RegisterService(sContent, False)

                    reply = msg.make_reply()
                    reply.body = " "
                    reply.set_metadata("performative", "inform")
                    await self.send(reply)

        template = Template()
        template.set_metadata("performative", "services")
        self.add_behaviour(CyclicBehaviourSR(), template)

    # Behaviour to handle Pack Management: Creation and Destruction
    def Launch_PackManagement_ResponderBehaviour(self):

        class CyclicBehaviourPM(Behaviour):
            async def run(self):
                msg = await self.receive(True)
                if msg:
                    sContent = msg.body
                    tokens = sContent.split()

                    id = int(tokens[1])
                    sAction = tokens[2]

                    if sAction.upper() == "DESTROY":
                        # Statistics
                        DinObject = self.agent.m_DinObjectList[id]
                        if DinObject.m_eTeam == CTroop.TEAM_ALLIED:
                            ePackTeam = 0
                        else:
                            ePackTeam = 1
                        ePackType = -1
                        if DinObject.m_eType == CPack.PACK_MEDICPACK:
                            ePackType = 0
                        elif DinObject.m_eType == CPack.PACK_AMMOPACK:
                            ePackType = 1
                        if ePackType >= 0:
                            self.agent.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[ePackType].m_iNotTaken=self.agent.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[ePackType].m_iNotTaken + 1
                        try:
                            del self.agent.m_DinObjectList[id]
                            print("Pack removed")
                        except:
                            print("Pack", str(id), "cannot be erased")
                        return

                    if sAction.upper() == "CREATE":

                        index = tokens.index("TYPE:") #// Get "TYPE:"
                        eType = int(tokens[index+1])

                        index = tokens.index("TEAM:") #// Get "TEAM:"
                        eTeam = int(tokens[index+1])

                        x = float(tokens[index+3]) #skip "("
                        y = float(tokens[index+5]) #skip ","
                        z = float(tokens[index+7]) #skip ","

                        DinObj = CDinObject()
                        DinObj.m_AID = msg.sender
                        DinObj.m_eType = eType
                        DinObj.m_eTeam = eTeam
                        DinObj.m_Position.x = x
                        DinObj.m_Position.y = y
                        DinObj.m_Position.z = z

                        self.agent.m_DinObjectList[DinObj.m_id] = DinObj
                        print("Added DinObject", str(DinObj))

                        reply = msg.make_reply()
                        reply.body = "ID: " + str(DinObj.m_id) + " "
                        await self.send(reply)

                        #/Statistics
                        if eTeam == CTroop.TEAM_ALLIED:
                            ePackTeam = 0
                        else:    ePackTeam = 1
                        ePackType = -1
                        if DinObj.m_eType == CPack.PACK_MEDICPACK:
                            ePackType = 0
                        elif DinObj.m_eType == CPack.PACK_AMMOPACK:
                            ePackType = 1

                        if ePackType >= 0:
                            self.agent.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[ePackType].m_iDelivered=self.agent.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[ePackType].m_iDelivered + 1

                    else:
                        print("Action not identified: " + str(sAction))
                        return

        template = Template()
        template.set_metadata("performative", "pack")
        self.add_behaviour(CyclicBehaviourPM(), template)

    # Behaviour to inform all agents that game has finished by time
    def Launch_GameTimeout_InformBehaviour(self):
        class TickerBehaviour(TimeoutBehaviour):
            async def run(self):
                print("\n\nManager:  GAME FINISHED!! Winner Team: AXIS! (Time Expired)\n")
                self.agent.InformGameFinished("AXIS!")

        self.add_behaviour(TickerBehaviour(self.m_lMatchTime))

    async def CheckObjectsAtStep(self, _idAgent, behaviour):

        if len(self.m_DinObjectList) <= 0:
            return

        if self.m_AgentList[_idAgent].m_iHealth <= 0:
            return

        WIDE = 3
        xmin = self.m_AgentList[_idAgent].m_Locate.m_Position.x - WIDE
        zmin = self.m_AgentList[_idAgent].m_Locate.m_Position.z - WIDE
        xmax = self.m_AgentList[_idAgent].m_Locate.m_Position.x + WIDE
        zmax = self.m_AgentList[_idAgent].m_Locate.m_Position.z + WIDE

        for DinObject in self.m_DinObjectList.values():
            if DinObject.m_eType == CPack.PACK_MEDICPACK and self.m_AgentList[_idAgent].m_iHealth >= 100: continue
            if DinObject.m_eType == CPack.PACK_AMMOPACK  and self.m_AgentList[_idAgent].m_iAmmo >= 100:   continue
            if DinObject.m_eType == CPack.PACK_OBJPACK   and DinObject.m_bTaken and DinObject.m_Owner >0: continue

            if  DinObject.m_Position.x >= xmin and DinObject.m_Position.x <= xmax \
            and DinObject.m_Position.z >= zmin and DinObject.m_Position.z <= zmax:

                # Agent has stepped on pack
                bSend = False
                id = DinObject.m_JID
                iQty = 0
                eType = DinObject.m_eType
                owner = DinObject.m_JID
                sContent = ""

                # Statistics
                eTeam = self.m_AgentList[_idAgent].m_eTeam
                if DinObject.m_eTeam == CTroop.TEAM_ALLIED:
                    ePackTeam = 0
                else:    ePackTeam = 1

                if DinObject.m_eType == CPack.PACK_MEDICPACK:
                    # Statistics
                    if DinObject.m_eTeam == eTeam:
                        self.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[0].m_iTeamTaken=\
                        self.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[0].m_iTeamTaken+1
                    else:
                        self.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[0].m_iEnemyTaken=\
                        self.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[0].m_iEnemyTaken+1

                    iQty = 20
                    try:
                        del self.m_DinObjectList[id]
                        print (self.m_AgentList[_idAgent].m_JID + ": got a medic pack " + str(DinObject.m_JID))
                        sContent = " TYPE: " + str(eType) + " QTY: " + str(iQty) + " "
                        bSend = True

                    except:
                        print("NO SE PUEDE BORRAR LA CLAVE")

                elif DinObject.m_eType == CPack.PACK_AMMOPACK:
                    # Statistics
                    if DinObject.m_eTeam == eTeam:
                        self.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[1].m_iTeamTaken=\
                        self.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[1].m_iTeamTaken+1
                    else:
                        self.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[1].m_iEnemyTaken=\
                        self.m_GameStatistic.m_tTeamStatistic[ePackTeam].m_iPacks[1].m_iEnemyTaken+1

                    iQty = 20
                    try:
                        del self.m_DinObjectList[id]
                        print (self.m_AgentList[_idAgent].m_JID + ": got an ammo pack " + str(DinObject.m_JID))
                        sContent = " TYPE: " + str(eType) + " QTY: " + str(iQty) + " "
                        bSend = True
                    except:
                        print("NO SE PUEDE BORRAR LA CLAVE")

                elif DinObject.m_eType == CPack.PACK_OBJPACK:

                    if self.m_AgentList[_idAgent].m_eTeam == CTroop.TEAM_ALLIED:
                        print(self.m_AgentList[_idAgent].m_JID + ": got the objective pack " + str(DinObject.m_JID))
                        DinObject.m_bTaken = True
                        DinObject.m_Owner = _idAgent
                        DinObject.m_Position.x = DinObject.m_Position.y = DinObject.m_Position.z = 0.0
                        self.m_AgentList[_idAgent].m_bCarryingObjective = True
                        sContent = " TYPE: " + str(eType) + " QTY: 0 TEAM: ALLIED "
                        bSend = True

                        # Statistics
                        self.m_GameStatistic.m_tTeamStatistic[0].m_iTotalObjectiveTaken = \
                        self.m_GameStatistic.m_tTeamStatistic[0].m_iTotalObjectiveTaken + 1
                        self.m_GameStatistic.m_tTeamStatistic[1].m_iTotalObjectiveLost  = \
                        self.m_GameStatistic.m_tTeamStatistic[1].m_iTotalObjectiveLost  + 1

                    elif self.m_AgentList[_idAgent].m_eTeam == CTroop.TEAM_AXIS:
                        if DinObject.m_bTaken:
                            print (self.m_AgentList[_idAgent].m_JID + ": returned the objective pack " + str(DinObject.m_JID))
                            DinObject.m_bTaken = False
                            DinObject.m_Owner = 0
                            DinObject.m_Position.x =self.m_Map.GetTargetX()
                            DinObject.m_Position.y =self.m_Map.GetTargetY()
                            DinObject.m_Position.z =self.m_Map.GetTargetZ()
                            sContent = " TYPE: " + str(eType) + " QTY: 0 TEAM: AXIS "
                            bSend = True

                            # Statistics
                            self.m_GameStatistic.m_tTeamStatistic[1].m_iTotalObjectiveTaken=\
                            self.m_GameStatistic.m_tTeamStatistic[1].m_iTotalObjectiveTaken+1
                else:
                    sContent = " TYPE: " + str(CPack.PACK_NONE) + " QTY: 0 "

                #// Send a destroy/taken msg to pack and an inform msg to agent
                if bSend:
                    msg = Message(to=owner)
                    msg.set_metadata("performative", "pack_taken")
                    msg.body=sContent
                    await behaviour.send(msg)

                    msg = Message(to=self.m_AgentList[_idAgent].m_AID)
                    msg.set_metadata("performative", "pack_taken")
                    msg.body = sContent
                    await behaviour.send(msg)

    def GetObjectsInFieldOfView(self, _idAgent):

        ObjectsInSight = list()
        a = None

        for agent in self.m_AgentList.values():
            if agent.m_JID == _idAgent:
                a = agent

        if a is None:
            return ObjectsInSight

        dotAngle = float(a.m_Locate.m_dAngle)

        # am I watching agents?
        for agent in self.m_AgentList.values():
            if agent.m_JID == _idAgent:
                continue
            if agent.m_iHealth <= 0:  # OJO, igual interesa ke veamos muertos :D
                continue

            v = Vector3D(v=agent.m_Locate.m_Position )
            v.sub(a.m_Locate.m_Position)

            distance = v.length()

            # comprobamos la distancia
            # miramos la distancia a la pared mas cercano
            dDistanceTerrain = self.intersect(a.m_Locate.m_Position, v)  # a.m_Locate.m_Heading)

            # comprobamos la distancia
            if distance < a.m_Locate.m_dViewRadius and distance < dDistanceTerrain:

                #testeamos el angulo
                angle = a.m_Locate.m_Heading.dot(v)
                try:
                    angle /= a.m_Locate.m_Heading.length() * v.length()
                except:
                    # Division BY ZEROOOOO!!!!
                    pass

                if angle >= 0:
                    if angle > 1: angle = 1
                    angle = math.acos(angle)
                    if angle <= dotAngle:
                        s = CSight()
                        s.m_dDistance = distance
                        s.m_id = agent.m_id
                        s.m_Position = agent.m_Locate.m_Position
                        s.m_eTeam = agent.m_eTeam
                        s.m_eType = agent.m_eType
                        s.m_dAngle = angle
                        s.m_iHealth = agent.m_iHealth
                        ObjectsInSight.append(s)

        # am I watching objects?
        if len(self.m_DinObjectList) > 0:

            for dinObject in self.m_DinObjectList.values():

                v = Vector3D(v=dinObject.m_Position)
                v.sub(a.m_Locate.m_Position)

                distance = v.length()

                # comprobamos la distancia
                # miramos la distancia a la pared mas cercano
                dDistanceTerrain = self.intersect(a.m_Locate.m_Position, v) #a.m_Locate.m_Heading)

                if distance < a.m_Locate.m_dViewRadius and distance < dDistanceTerrain:

                    angle = a.m_Locate.m_Heading.dot(v)
                    angle /= (a.m_Locate.m_Heading.length() * v.length())
                    if angle >= 0:
                        if angle > 1: angle = 1
                        angle = math.acos(angle)
                        if angle <= dotAngle:
                            s = CSight()
                            s.m_dDistance = distance
                            s.m_id = int(dinObject.m_id)
                            s.m_Position = dinObject.m_Position
                            s.m_eTeam = dinObject.m_eTeam
                            s.m_eType = dinObject.m_eType
                            s.m_dAngle = angle
                            s.m_iHealth = -1
                            ObjectsInSight.append(s)

        return ObjectsInSight

    # El agente con id '_idAgent' dispara
    # mejor pasar el agente?
    # @return el agente al que ha dado, o null si nada
    def Shot(self, _idAgent):

        s = None
        minDistance = 1e10 #numero grande :-)

        a = None

        for agent in self.m_AgentList.values():
            if agent.m_JID == _idAgent:
                a = agent
                break

        if a == None:
            return None
            #return -1

        # agentes
        for agent in self.m_AgentList.values():
            if agent.m_JID == _idAgent: continue

            if agent.m_iHealth <= 0: continue

            p = Vector3D(v=a.m_Locate.m_Position)

            p.sub(agent.m_Locate.m_Position)

            dv = p.dot(a.m_Locate.m_Heading)
            d2 = a.m_Locate.m_Heading.dot(a.m_Locate.m_Heading)
            sq = (dv * dv) - ((d2 * p.dot(p)) - 4)

            if sq >= 0:

                sq = math.sqrt(sq)
                dist1 = (-dv + sq) / d2
                dist2 = (-dv - sq) / d2
                if dist1 < dist2: distance = dist1
                else: distance = dist2

                if distance > 0 and distance < minDistance:
                    minDistance = distance
                    s = agent

        if s != None:
            v = Vector3D(v=s.m_Locate.m_Position)
            v.sub(a.m_Locate.m_Position)
            dDistanceTerrain = self.intersect(a.m_Locate.m_Position, a.m_Locate.m_Heading)
            #print "distanceTerrain: " + str(dDistanceTerrain)
            if dDistanceTerrain != 0.0 and dDistanceTerrain < minDistance:
                s = None

        return s

    # devuelve 0.0 si no intersecta
    def intersect(self, origin, vector):

        try:
            step = Vector3D(v=vector)
            step.normalize()
            inc = 0
            sgn = 1.0
            e   = 0.0

            if abs(step.x) > abs(step.z):

                if step.z < 0: sgn = -1

                step.x /= abs(step.x)
                step.z /= abs(step.x)
            else:

                if step.x < 0: sgn = -1

                inc = 1
                step.x /= abs(step.z)
                step.z /= abs(step.z)

            error = Vector3D(x=0, y=0, z=0)
            point = Vector3D(v=origin)


            while True:

                if inc == 0:

                    if e + abs(step.z) + 0.5 >= 1:
                        point.z += sgn
                        e -= 1

                    e += abs(step.z)
                    point.x += step.x
                else:

                    if e + abs(step.x) + 0.5 >= 1:
                        point.x+=sgn
                        e-= 1

                    e += abs(step.x)
                    point.z += step.z

                if not self.m_Map.CanWalk(int(math.floor(point.x/8)), int(math.floor(point.z/8))):
                    return error.length()

                if point.x < 0 or point.y < 0 or point.z < 0:
                    break
                if  point.x >= (self.m_Map.GetSizeX() * 8) or point.z >= (self.m_Map.GetSizeZ() * 8):
                    break
                error.add(step)
        except:
            print("INTERSECT FAILED", origin, vector)

        return 0.0

    def CheckGameFinished(self, _idAgent):

        if self.m_AgentList[_idAgent].m_eTeam == CTroop.TEAM_AXIS: return False
        if self.m_AgentList[_idAgent].m_bCarryingObjective == False: return False

        if self.m_AgentList[_idAgent].m_Locate.m_Position.x > self.m_Map.m_AlliedBase.m_Init.x and \
                self.m_AgentList[_idAgent].m_Locate.m_Position.z > self.m_Map.m_AlliedBase.m_Init.z and \
                self.m_AgentList[_idAgent].m_Locate.m_Position.x < self.m_Map.m_AlliedBase.m_End.x and \
                self.m_AgentList[_idAgent].m_Locate.m_Position.z < self.m_Map.m_AlliedBase.m_End.z:

            return True
        return False

    def CreateObjectives(self):

        self.ObjectiveAgent = CObjPack("objectivepack@"+self.m_domain, "secret", self.m_Map.GetTargetX() / 8, self.m_Map.GetTargetZ() / 8, CTroop.TEAM_NONE)
        self.ObjectiveAgent.start()


    async def InformObjectives(self, behaviour):

        msg = Message()
        msg.set_metadata("performative", "objective")
        msg.body = " ( " + str(self.m_Map.GetTargetX()) + " , " + str(self.m_Map.GetTargetY()) + " , " + str(
            self.m_Map.GetTargetZ()) + " ) "
        for agent in self.m_AgentList.values():
            msg.to = agent.m_JID
            await behaviour.send(msg)
        print("Manager: Sending Objective notification to agents")

    async def InformGameFinished(self, _sWinnerTeam, behaviour):

        msg = Message()
        msg.set_metadata("performative", "game")
        msg.body = " GAME FINISHED!! Winner Team: " + str(_sWinnerTeam)
        for agent in self.m_AgentList.values():
            msg.to = agent.m_sName
            await behaviour.send(msg)
        for st in self.m_REServer.m_ConnectionList:
            try:
                st.SendMsgToRenderEngine(CServer.CRequestHandler.TCP_COM, "FINISH " +
                                         " GAME FINISHED!! Winner Team: " + str(_sWinnerTeam))
            except:
                pass

        self.PrintStatistics(_sWinnerTeam)

        del self.m_REServer
        self.m_REServer = None
        self.take_down()

    def PrintStatistics(self, _sWinnerTeam):

        iAlliedAlivePlayers = 0
        iAxisAlivePlayers = 0
        iAlliedHealth = 0
        iAxisHealth = 0

        self.m_GameStatistic.m_lMatchDuration = time.time() * 1000
        self.m_GameStatistic.m_lMatchDuration -= self.m_lMatchInit

        for agent in self.m_AgentList.values():
            if agent.m_eTeam == CTroop.TEAM_ALLIED:
                iAlliedHealth += agent.m_iHealth
                if agent.m_iHealth > 0:
                    iAlliedAlivePlayers = iAlliedAlivePlayers + 1
            else:
                iAxisHealth += agent.m_iHealth
                if agent.m_iHealth > 0:
                    iAxisAlivePlayers = iAxisAlivePlayers +1

        self.m_GameStatistic.CalculateData(iAlliedAlivePlayers, iAxisAlivePlayers, iAlliedHealth, iAxisHealth)

        try:
            fw = open("JGOMAS_Statistics.txt",'w+')

            fw.write(self.m_GameStatistic.__str__(_sWinnerTeam))

            fw.close()

        except:
            print("COULD NOT WRITE STATISTICS TO FILE")
