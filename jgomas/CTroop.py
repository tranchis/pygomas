import random
import time
import threading
from spade.message import Message
from spade.behaviour import OneShotBehaviour, PeriodicBehaviour, FSMBehaviour, State
from spade.template import Template
from jgomas.CJGomasAgent import CJGomasAgent
from jgomas.CThreshold import CThreshold
from jgomas.CTerrainMap import CTerrainMap
from jgomas.CMobile import CMobile
from jgomas.CTask import CTask
from jgomas.Vector3D import Vector3D
from jgomas.CSight import CSight
from jgomas.CPack import CPack
from jgomas.CConfig import CConfig


class CTroop(CJGomasAgent):

    ARG_TEAM = 0

    TEAM_NONE = 0
    TEAM_ALLIED = 100
    TEAM_AXIS = 200

    CLASS_NONE = 0
    CLASS_SOLDIER = 1
    CLASS_MEDIC = 2
    CLASS_ENGINEER = 3
    CLASS_FIELDOPS = 4

    # State names
    STATE_STANDING = "STATE_STANDING"
    STATE_TARGET_REACHED = "STATE_TARGET_REACHED"
    STATE_FIGHTING = "STATE_FIGHTING"
    STATE_QUIT = "STATE_QUIT"
    STATE_GOTO_TARGET = "STATE_GOTO_TARGET"  # This one was missing

    TRANSITION_DEFAULT = 0
    TRANSITION_TO_STANDING = 1  # STANDING
    TRANSITION_TO_GOTO_TARGET = 2  # GOTO TARGET
    TRANSITION_TO_TARGET_REACHED = 3  # TARGET REACHED
    TRANSITION_TO_FIGHTING = 4  # FIGHTING
    TRANSITION_TO_QUIT = 5  # BYE

    MV_OK = 0
    MV_CANNOT_GET_POSITION = 1
    MV_NOT_MOVED_BY_TIME = 2

    MEDIC_SERVICE = "medic"
    AMMO_SERVICE = "ammo"
    BACKUP_SERVICE = "backup"

    def __init__(self, jid, passwd, team=TEAM_NONE, manager_jid="cmanager@localhost", service_jid="cservice@localhost"):

        # Task List Lock
        self.m_TaskListLock = threading.Lock()

        self.m_ServiceType = []

        # Variable used to store the AID of Manager
        self.m_Manager = manager_jid
        self.m_Service = service_jid

        # List of prepared to execut tasks
        self.m_TaskList = {}

        # Variable used to point the current task in execution
        self.m_CurrentTask = None

        # Variable indicating if this agent is carrying the objective pack (flag)
        self.m_bObjectiveCarried = False

        # Array of default values of priorities for each task
        self.m_TaskPriority = {}

        # Array of points used in patrolling task
        self.m_ControlPoints = []

        # Current position in array m_ControlPoints
        self.m_iControlPointsIndex = 0

        # Array of points used in walking (a calculated) path task
        self.m_AStarPath = []

        # Current position in array m_AStarPath
        self.m_iAStarPathIndex = 0

        # List of objects in the agent's Field Of Vision
        self.m_FOVObjects = []

        # Current aimed enemy
        self.m_AimedAgent = None  # CSight

        self.m_eClass = 0
        self.m_iHealth = 0
        self.m_iProtection = 0
        self.m_iStamina = 0
        self.m_iPower = 0
        self.m_iAmmo = 0

        # Variable indicating if agent is fighting at this moment
        self.m_bFighting = False

        # Variable indicating if agent is escaping at this moment
        self.m_bEscaping = False

        # Current position, direction, and so on...
        self.m_Movement = None  # CMobile

        self.m_iSoldiersCount = 0
        self.m_iMedicsCount = 0
        self.m_iEngineersCount = 0
        self.m_iFieldOpsCount = 0
        self.m_iTeamCount = 0

        # Limits of some variables (to trigger some events)
        self.m_Threshold = CThreshold()  # CThreshold

        # Current Map
        self.m_Map = None  # CTerrainMap

        self.m_FSM = None  # FSMBehaviour

        CJGomasAgent.__init__(self, jid, passwd, team=team)

    def start(self, auto_register=True):
        CJGomasAgent.start(self, auto_register)

        self.m_iHealth = 100
        self.m_iProtection = 25
        self.m_iStamina = 100
        self.m_iPower = 100
        self.m_iAmmo = 100

        # Send a welcome message, and wait for the beginning of match
        self.add_behaviour(self.CreateBasicTroopBehaviour())

        t = Template()
        t.set_metadata("performative", "init")
        self.add_behaviour(self.InitResponderBehaviour(), t)

    class CreateBasicTroopBehaviour(OneShotBehaviour):
        async def run(self):
            if self.agent.m_ServiceType is not None:
                for service in self.agent.m_ServiceType:
                    self.agent.register_service(str(service))

            msg = Message(to=self.agent.m_Manager)
            msg.set_metadata("performative", "init")
            msg.body = "NAME: " + self.agent.name + " TYPE: " + str(self.agent.m_eClass) + \
                       " TEAM: " + str(self.agent.m_eTeam) + " HELLO!"
            await self.send(msg)

    class InitResponderBehaviour(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1000000)
            if msg is None:
                print("[" + self.agent.name + "]: Warning! Cannot begin")
                self.agent.stop()
                return
            else:
                tokens = msg.body.split()
                s_map_name = None
                for token in tokens:
                    if token == "MAP:":
                        s_map_name = tokens[tokens.index(token) + 1]
                print("[" + self.agent.name + "]: Beginning to fight")
                if not s_map_name:
                    return
                self.agent.m_Map = CTerrainMap()
                config = CConfig()
                self.agent.m_Map.LoadMap(s_map_name, config)
                self.agent.m_Movement = CMobile()
                self.agent.m_Movement.SetSize(self.agent.m_Map.GetSizeX(), self.agent.m_Map.GetSizeZ())

                self.agent.generate_spawn_position()
                self.agent.SetUpPriorities()

                # Behaviour to get the objective of the game, to create the corresponding task
                t = Template()
                t.set_metadata("performative", "objective")
                self.agent.add_behaviour(self.agent.ObjectiveBehaviour(), t)

                # Behaviour to listen to manager if game has finished
                t = Template()
                t.set_metadata("performative", "game")
                self.agent.add_behaviour(self.agent.GameFinishedBehaviour(), t)

                # Behaviour to handle Pack Taken messages
                t = Template()
                t.set_metadata("performative", "pack_taken")
                self.agent.add_behaviour(self.agent.PackTakenBehaviour(0), t)

                # Behaviour to handle Shot messages
                t = Template()
                t.set_metadata("performative", "shot")
                self.agent.add_behaviour(self.agent.PackTakenBehaviour(0), t)

                # Behaviour to inform JGomasManager our position, status, and so on
                self.agent.add_behaviour(self.agent.DataFromTroopBehaviour(0.1))

                # Behaviour to increment inner variables (Power, Stamina and Health Bars)
                #self.agent.Launch_BarsAddOn_InnerBehaviour()
                self.agent.add_behaviour(self.agent.RestoreBehaviour(1))

                # Behaviour to call for medics or fieldops
                self.agent.add_behaviour(self.agent.MedicAmmoRequestBehaviour(1))

                # // Behaviour to launch the FSM
                self.agent.Launch_FSM_Behaviour()

    # Behaviour to get the objective of the game, to create the corresponding task
    class ObjectiveBehaviour(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1000000)
            if msg:
                if self.agent.m_eTeam == self.agent.TEAM_ALLIED:
                    self.agent.AddTask(CTask.TASK_GET_OBJECTIVE, self.agent.name, msg.body)
                    print("### ALIADO SABE DONDE IR", self.agent.name, msg.body)
                elif self.agent.m_eTeam == self.agent.TEAM_AXIS:
                    self.agent.CreateControlPoints()
                    s_new_position = " ( " + str(self.agent.m_ControlPoints[0].x) + " , " + \
                                     str(self.agent.m_ControlPoints[0].y) + " , " + \
                                     str(self.agent.m_ControlPoints[0].z) + " ) "
                    self.agent.AddTask(CTask.TASK_PATROLLING, self.agent.name, s_new_position)
                    print("### EJE SABE DONDE IR", self.agent.name, str(s_new_position))

    # Behaviour to listen to manager if game has finished
    class GameFinishedBehaviour(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1000000)
            if msg:
                print("[" + self.agent.name + "]: Bye! (v55)")
                self.agent.take_down()

    # Behaviour to handle Pack Taken messages
    class PackTakenBehaviour(PeriodicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1000000)
            if msg:
                # Agent has stepped on pack
                print("PACK TAKEN:", msg.body)
                s_content = msg.body
                tokens = s_content.split()
                e_type = int(tokens[1])
                i_qty = int(tokens[3])

                if e_type == CPack.PACK_MEDICPACK:
                    self.agent.IncHealth(i_qty)
                elif e_type == CPack.PACK_AMMOPACK:
                    self.agent.IncAmmo(i_qty)
                elif e_type == CPack.PACK_OBJPACK:
                    self.agent.ObjectivePackTaken()
                    if self.agent.m_eTeam == self.agent.TEAM_ALLIED:
                        self.agent.m_bObjectiveCarried = True
                        x = ((self.agent.m_Map.m_AlliedBase.GetEndX() -
                              self.agent.m_Map.m_AlliedBase.GetInitX()) / 2) + \
                            self.agent.m_Map.m_AlliedBase.GetInitX()
                        y = ((self.agent.m_Map.m_AlliedBase.GetEndY() -
                              self.agent.m_Map.m_AlliedBase.GetInitY()) / 2) + \
                            self.agent.m_Map.m_AlliedBase.GetInitY()
                        z = ((self.agent.m_Map.m_AlliedBase.GetEndZ() -
                              self.agent.m_Map.m_AlliedBase.GetInitZ()) / 2) + \
                            self.agent.m_Map.m_AlliedBase.GetInitZ()
                        s_new_position = " ( " + str(x) + " , " + str(y) + " , " + str(z) + " ) "
                        self.agent.AddTask(CTask.TASK_GET_OBJECTIVE, self.agent.name, s_new_position)

    # Behaviour to handle Shot messages
    class ShotBehaviour(PeriodicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1000000)
            if msg:
                s_content = msg.body
                tokens = s_content.split()
                i_dec_health = int(tokens[1])

                self.agent.DecHealth(i_dec_health)
                if self.agent.m_iHealth <= 0:
                    print(self.agent.getName() + ": DEAD!!")
                    self.agent.m_TaskListLock.acquire()
                    self.agent.m_TaskList = {}
                    self.agent.m_TaskListLock.release()
                    if self.agent.m_bObjectiveCarried:
                        self.agent.m_bObjectiveCarried = False
                    self.agent.take_down()

                self.agent.PerformInjuryAction()

    # Behaviour to inform JGomasManager our position, status, and so on
    class DataFromTroopBehaviour(PeriodicBehaviour):
        async def run(self):
            s_content = "NAME: " + str(self.agent.name) + " ( " + \
                        str(self.agent.m_Movement.m_Position.x) + " , " + \
                        str(self.agent.m_Movement.m_Position.y) + " , " + \
                        str(self.agent.m_Movement.m_Position.z) + " ) "
            s_content += "( " + str(self.agent.m_Movement.m_Velocity.x) + " , " + \
                         str(self.agent.m_Movement.m_Velocity.y) + " , " + \
                         str(self.agent.m_Movement.m_Velocity.z) + " ) "
            s_content += "( " + str(self.agent.m_Movement.m_Heading.x) + " , " + \
                         str(self.agent.m_Movement.m_Heading.y) + " , " + \
                         str(self.agent.m_Movement.m_Heading.z) + " ) "
            s_content += "HEALTH: " + str(self.agent.m_iHealth) + " AMMO: " + str(self.agent.m_iAmmo) + " "
            msg = Message(to=self.agent.m_Manager)
            msg.set_metadata("performative", "data")
            msg.body = s_content
            print(s_content)
            await self.send(msg)

    # Behaviour to increment inner variables (Power, Stamina and Health Bars)
    class RestoreBehaviour(PeriodicBehaviour):
        async def run(self):
            if self.agent.m_iStamina < 100:
                self.agent.m_iStamina = self.agent.m_iStamina + 1

            if self.agent.m_iPower < 100:
                self.agent.m_iPower = self.agent.m_iPower + 1

            if self.agent.m_eClass == self.agent.CLASS_MEDIC and self.agent.m_iHealth > 0:
                if self.agent.m_iHealth < 100:
                    self.agent.m_iHealth = self.agent.m_iHealth + 1

    # Behaviour to call for medics or fieldops
    class MedicAmmoRequestBehaviour(PeriodicBehaviour):
        async def run(self):
            b_low_level = False
            if self.agent.m_iHealth < self.agent.m_Threshold.GetHealth():
                b_low_level = True
                self.agent.CallForMedic(self)

            if self.agent.m_iAmmo < self.agent.m_Threshold.GetAmmo():
                b_low_level = True
                self.agent.CallForAmmo(self)

            if b_low_level:
                self.agent.PerformThresholdAction()

    # Behaviour to launch the FSM
    def Launch_FSM_Behaviour(self):

        # FSM Declaration
        self.m_FSM = FSMBehaviour()

        # Register state STATE_STANDING (first state)
        self.m_FSM.add_state(self.STATE_STANDING, self.FSM_Standing(), initial=True)

        # Register state STATE_GOTO_TARGET
        self.m_FSM.add_state(self.STATE_GOTO_TARGET, self.FSM_GoToTarget())

        # Register state STATE_TARGET_REACHED
        self.m_FSM.add_state(self.STATE_TARGET_REACHED, self.FSM_TargetReached())

        # Register state STATE_FIGHTING
        self.m_FSM.add_state(self.STATE_FIGHTING, self.FSM_Fighting())

        # Register state STATE_QUIT (final state)
        self.m_FSM.add_state(self.STATE_QUIT, self.FSM_Quit())

        # Register the transitions
        # m_FSM.registerDefaultTransition(STATE_STANDING, STATE_QUIT);
        # self.m_FSM.registerDefaultTransition(self.STATE_STANDING, self.STATE_STANDING) ## OJO
        self.m_FSM.add_transition(self.STATE_STANDING, self.STATE_STANDING)
        self.m_FSM.add_transition(self.STATE_STANDING, self.STATE_GOTO_TARGET)
        self.m_FSM.add_transition(self.STATE_STANDING, self.STATE_QUIT)

        # self.m_FSM.registerDefaultTransition(self.STATE_GOTO_TARGET, self.STATE_GOTO_TARGET)
        self.m_FSM.add_transition(self.STATE_GOTO_TARGET, self.STATE_GOTO_TARGET)
        self.m_FSM.add_transition(self.STATE_GOTO_TARGET, self.STATE_STANDING)
        self.m_FSM.add_transition(self.STATE_GOTO_TARGET, self.STATE_TARGET_REACHED)
        self.m_FSM.add_transition(self.STATE_GOTO_TARGET, self.STATE_FIGHTING)

        # self.m_FSM.registerDefaultTransition(self.STATE_TARGET_REACHED, self.STATE_STANDING)
        self.m_FSM.add_transition(self.STATE_TARGET_REACHED, self.STATE_STANDING)
        self.m_FSM.add_transition(self.STATE_TARGET_REACHED, self.STATE_STANDING)

        # self.m_FSM.registerDefaultTransition(self.STATE_FIGHTING, self.STATE_FIGHTING)
        self.m_FSM.add_transition(self.STATE_FIGHTING, self.STATE_FIGHTING)
        self.m_FSM.add_transition(self.STATE_FIGHTING, self.STATE_STANDING)

        # launching the FSM
        self.add_behaviour(self.m_FSM)

    def generate_spawn_position(self):

        if self.m_eTeam == self.TEAM_ALLIED:
            w = self.m_Map.m_AlliedBase.m_End.x - self.m_Map.m_AlliedBase.m_Init.x
            h = self.m_Map.m_AlliedBase.m_End.z - self.m_Map.m_AlliedBase.m_Init.z
            d_offset_x = self.m_Map.m_AlliedBase.m_Init.x
            d_offset_z = self.m_Map.m_AlliedBase.m_Init.z

        else:
            w = self.m_Map.m_AxisBase.m_End.x - self.m_Map.m_AxisBase.m_Init.x
            h = self.m_Map.m_AxisBase.m_End.z - self.m_Map.m_AxisBase.m_Init.z
            d_offset_x = self.m_Map.m_AxisBase.m_Init.x
            d_offset_z = self.m_Map.m_AxisBase.m_Init.z

        x = (random.random() * w) + d_offset_x
        z = (random.random() * h) + d_offset_z

        self.m_Movement.m_Position.x = x
        self.m_Movement.m_Position.y = 0
        self.m_Movement.m_Position.z = z

    def move(self, _dt):
        p = Vector3D()
        p.x = self.m_Movement.m_Position.x
        p.y = self.m_Movement.m_Position.y
        p.z = self.m_Movement.m_Position.z

        if self.m_Movement.CalculatePosition(_dt):

            if not self.CheckStaticPosition():
                self.m_Movement.m_Position.x = p.x
                self.m_Movement.m_Position.y = p.y
                self.m_Movement.m_Position.z = p.z
                print(self.name + ": No puedo andar : (" +
                      str(self.m_Movement.m_Position.x) + ", " +
                      str(self.m_Movement.m_Position.z) + ")")
                return self.MV_CANNOT_GET_POSITION
            return self.MV_OK
        return self.MV_NOT_MOVED_BY_TIME

    # Behaviours to handle our FSM
    class FSM_Standing(State):
        async def run(self):
            self.agent.m_TaskListLock.acquire()
            tllen = len(self.agent.m_TaskList)
            self.agent.m_TaskListLock.release()
            if tllen <= 0:

                self._exitcode = self.agent.TRANSITION_DEFAULT
                print(self.agent.name + ": Behaviour ............ NO TASKS!!!")
                time.sleep(1)
                return self.agent.TRANSITION_DEFAULT

            if self.agent.m_iHealth <= 0:
                self.agent.m_TaskListLock.acquire()
                self.agent.m_TaskList = {}
                self.agent.m_TaskListLock.release()
                self._exitcode = self.agent.TRANSITION_DEFAULT  # if we have nothing to do, go to QUIT state

                return self._exitcode

            self.agent.UpdateTargets()

            i_max_priority = -100000
            self.agent.m_TaskListLock.acquire()
            for Task in self.agent.m_TaskList.values():
                if Task.m_iPriority > i_max_priority:
                    i_max_priority = Task.m_iPriority
                    print(self.agent.name + ": nos quedamos con la tarea con prioridad "+str(Task))
                    self.agent.m_CurrentTask = Task
            self.agent.m_TaskListLock.release()

            self.agent.m_Movement.m_Destination.x = self.agent.m_CurrentTask.m_Position.x
            self.agent.m_Movement.m_Destination.y = self.agent.m_CurrentTask.m_Position.y
            self.agent.m_Movement.m_Destination.z = self.agent.m_CurrentTask.m_Position.z

            self.agent.m_Movement.CalculateNewOrientation()
            self._exitcode = self.agent.TRANSITION_TO_GOTO_TARGET

            return self.agent.TRANSITION_TO_GOTO_TARGET

    class FSM_Quit(State):
        async def run(self):
            print(self.agent.name + ": Behaviour ............ [QUIT]")
            self.agent.take_down()
            return

    class FSM_GoToTarget(State):

        m_bInit = False

        async def run(self):

            if not self.m_bInit:
                self.agent.m_lLastTimeMove = self.agent.m_lLastTimeLook = time.time()
                self.m_bInit = True

            self._exitcode = self.agent.TRANSITION_DEFAULT  # GOTO_TARGET

            l_current_time = time.time()
            dt = l_current_time - self.agent.m_lLastTimeLook
            if dt > 0.500:
                self.agent.m_lLastTimeLook = l_current_time
                self.agent.Look()
                self.agent.PerformLookAction()
                self.agent.GetAgentToAim()
                if self.agent.HaveAgentToShot():
                    current_destination = self.agent.m_Movement.m_Destination
                    self.agent.PerformAimAction()
                    if not self.agent.Shot(0):
                        self.agent.PerformNoAmmoAction()
                    self.agent.m_Movement.m_Destination = current_destination
                    self.agent.m_lLastTimeMove = l_current_time
                    return self._exitcode

            dt = l_current_time - self.agent.m_lLastTimeMove
            if dt < 0.033:
                return self._exitcode
            self.agent.m_lLastTimeMove = l_current_time

            i_move_result = self.agent.move(dt)

            if i_move_result == self.agent.MV_OK:
                absx = abs(self.agent.m_Movement.m_Destination.x - self.agent.m_Movement.m_Position.x)
                absz = abs(self.agent.m_Movement.m_Destination.z - self.agent.m_Movement.m_Position.z)
                if (absx < 0.5) and (absz < 0.5):
                    self.agent.m_Movement.m_Position.x = self.agent.m_Movement.m_Destination.x
                    self.agent.m_Movement.m_Position.z = self.agent.m_Movement.m_Destination.z
                    self._exitcode = self.agent.TRANSITION_TO_TARGET_REACHED
                else:
                    if self.agent.ShouldUpdateTargets():
                        self._exitcode = self.agent.TRANSITION_TO_STANDING

            elif i_move_result == self.agent.MV_CANNOT_GET_POSITION:
                if self.agent.GeneratePath():
                    self._exitcode = self.agent.TRANSITION_TO_STANDING

            elif i_move_result == self.agent.MV_NOT_MOVED_BY_TIME:
                pass

            return self._exitcode

    class FSM_TargetReached(State):

        async def run(self):

            print(self.agent.getName() + ": Behaviour ............ [TARGET REACHED]")

            self.agent.PerformTargetReached(self.agent.m_CurrentTask)

            if self.agent.m_CurrentTask.m_bErasable:
                self.agent.m_TaskListLock.acquire()
                del self.agent.m_TaskList[self.agent.m_CurrentTask.m_iType]
                self.agent.m_TaskListLock.release()

            self._exitcode = self.agent.TRANSITION_TO_STANDING

            return self.agent.TRANSITION_TO_STANDING

    class FSM_Fighting(State):

        async def run(self):
            print(self.agent.getName() + ": Behaviour ............ [FIGHTING]")
            return self.agent.TRANSITION_DEFAULT

    # Non-overloadable Methods, interesting for user

    '''/**
     * Get the current health of the agent.
     *
     * @return m_iHealth: current value for health
     *
     */'''
    def get_health(self):
        return self.m_iHealth

    '''/**
     * Increments the current health of the agent.
     *
     * @param _iQty: positive quantity to increment
     *
     */'''
    def inc_health(self, i_qty):
        self. m_iHealth += i_qty
        if self.m_iHealth > 100:
            self.m_iHealth = 100

    '''/**
     * Decrements the current health of the agent.
     *
     * @param _iQty: negative quantity to decrement
     *
     */'''
    def dec_health(self, i_qty):
        self.m_iHealth -= i_qty
        if self.m_iHealth < 0:
            self.m_iHealth = 0

    '''/**
     * Get the current ammunition of the agent.
     *
     * @return m_iAmmo: current value for ammo
     *
     */'''
    def get_ammo(self):
        return self.m_iAmmo

    '''/**
     * Increments the current ammunition of the agent.
     *
     * @param _iQty: positive quantity to increment
     *
     */'''
    def inc_ammo(self, i_qty):
        self.m_iAmmo += i_qty
        if self.m_iAmmo > 100:
            self.m_iAmmo = 100

    '''/**
     * Decrements the current ammunition of the agent.
     *
     * @param _iQty: negative quantity to decrement
     *
     */'''
    def dec_ammo(self, i_qty):
        self.m_iAmmo -= i_qty
        if self.m_iAmmo < 0:
            self.m_iAmmo = 0

    '''/**
     * Get the current stamina of the agent.
     *
     * @return m_iStamina: current value for stamina bar
     *
     */'''
    def get_stamina(self):
        return self.m_iStamina

    '''/**
     * Use stamina from the stamina bar if possible (there is at least 5 units).
     *
     */'''
    def use_stamina(self):
        self.m_iStamina -= 5
        if self.m_iStamina <= 0:
            self.m_iStamina = 0

    '''/**
     * Get the current power of the agent.
     *
     * @return m_iPower: current value for power bar
     *
     */'''
    def get_power(self):
        return self.m_iPower

    '''/**
     * Use power from the power bar if possible (there is at least 25 units).
     *
     * Power bar is reduced in 25 units.
     *
     */'''
    def use_power(self):
        self.m_iPower -= 25
        if self.m_iPower <= 0:
            self.m_iPower = 0

    '''/**
     * Adds a type of service to the service type list.
     *
     * This method registers all types of services to offer in a list, excluding repeated services.
     *
     * @param _sServiceType
     *
     */'''
    def add_service_type(self, service_list):

        if not self.m_ServiceType:
            self.m_ServiceType = []

        if service_list.lower() not in self.m_ServiceType:
            self.m_ServiceType.append(service_list.lower())

    '''/**
     * Checks a position on the static map.
     *
     * This method checks if a position on the static map is valid to walk on, and returns the result.
     *
     * @param _x
     * @param _z
     * @return <tt> TRUE</tt> (agent can walk on) | <tt> FALSE</tt> (agent cannot walk on)
     *
     */'''
    def CheckStaticPosition(self, _x=None, _z=None):
        if not _x:
            _x = self.m_Movement.m_Position.x
        if not _z:
            _z = self.m_Movement.m_Position.z

        x = int(int(_x) / 8)
        z = int(int(_z) / 8)
        return self.m_Map.CanWalk(x, z)

    '''/**
     * Adds a task to the task list with a modified priority.
     *
     * This method adds a task to the task list with the priority passed as parameter, non the standard priority.
     * If there is a task of same type and same owner, it doesn't create a new task:
     * simply substitutes some attributes with newer values.
     *
     *
     * @param _tTypeOfTask one of the defined types of tasks.
     * @param _Owner the agent that induces the creation of the task.
     * @param _sContent is a position: <tt> ( x , y , z ) </tt>.
     * @param _iPriority priority of task
     *
     */'''
    def AddTask(self, _tTypeOfTask, owner, s_content, i_Priority=None):
        self.m_TaskListLock.acquire()
        if i_Priority is None:
            i_Priority = self.m_TaskPriority[_tTypeOfTask]

        bCreateTask = True

        # Check if we have an older task of the same type from this sender
        """
        for Task in self.m_TaskList.items():
            if Task.m_AID == _Owner:
                if Task.m_iType == _tTypeOfTask:
                    bCreateTask = False
                    break
        """
        if _tTypeOfTask in self.m_TaskList.keys():
            bCreateTask = False
            Task = self.m_TaskList[_tTypeOfTask]

        if bCreateTask:
            Task = CTask()
            Task.m_AID = owner
            Task.m_iType = _tTypeOfTask
            if _tTypeOfTask in [CTask.TASK_PATROLLING,CTask.TASK_GET_OBJECTIVE,CTask.TASK_WALKING_PATH]:
                Task.m_bErasable = False

        Task.m_iPriority = i_Priority
        Task.m_StampTime = time.time()

        tokens = s_content.split()
        Task.m_Position.x = float(tokens[1])
        Task.m_Position.y = float(tokens[3])
        Task.m_Position.z = float(tokens[5])

        """
        if bCreateTask:
            self.m_TaskList[Task.m_id] = Task
        """
        self.m_TaskList[Task.m_iType] = Task
        self.m_TaskListLock.release()

    '''/**
     * The agent looks in the direction he is walking.
     *
     * This method sends a <b> FIPA INFORM </b> message to Manager. Once message is sent, agent will be blocked
     * waiting a response message from Manager. The content of received message is stored in the variable <tt> m_FOVObjects</tt>.
     *
     */'''
    def Look(self):
        class LookBehaviour(OneShotBehaviour):
            async def run(self):
                msg = Message()
                msg.set_metadata('performative','sight')
                msg.to = self.agent.name
                msg.body = "NAME: " + self.agent.name
                self.send(msg)
                msgSight = await self.receive(10000)
                if not msgSight:
                    self.agent.m_AimedAgent = None
                    return

                sContent = msgSight.body

                tokens = sContent.split()
                iNumOfObjects = int(tokens[1])

                self.agent.m_FOVObjects = []

                if iNumOfObjects <= 0:
                    self.agent.m_AimedAgent = None
                    return

                tokens = tokens[2:]

                for i in range(iNumOfObjects):
                    s = CSight()
                    s.m_id = i
                    s.m_eTeam = int(tokens[1])
                    s.m_eType = int(tokens[3])
                    s.m_dAngle = float(tokens[5])
                    s.m_dDistance = float(tokens[7])
                    s.m_iHealth = int(tokens[9])
                    s.m_Position.x = float(tokens[11])
                    s.m_Position.y = float(tokens[13])
                    s.m_Position.z = float(tokens[15])
                    self.agent.m_FOVObjects.append(s)

        template = Template()
        template.set_metadata('performative','sight')
        b = LookBehaviour()
        self.add_behaviour(b, template)

    '''/**
     * The agent shoots in the direction which he is aiming.
     *
     * This method sends a <b> FIPA INFORM </b> message to Manager.
     * Once message is sent, the variable <tt> m_iAmmo</tt> is decremented.
     *
     * @param _iShotNum
     * @return <tt> TRUE</tt> (shot done) | <tt> FALSE</tt> (cannot shoot, has no ammo)
     *
     */'''
    def Shot(self, _iShotNum):
        class ShotBehaviour(OneShotBehaviour):
            async def run(self):
                if self.agent.m_iAmmo <= 0:
                    return False

                if self.agent.m_AimedAgent is None:
                    print (self.agent.name + ": queria disparar sin nadie a quien apuntar :-P")
                    return False

                # Fill the REQUEST message
                msg = Message()
                msg.to = self.agent.m_Manager
                msg.set_metadata('performative', 'shot')
                msg.body = "NAME: " + str(self.agent.name) + " AIM: " + str(self.agent.m_Threshold.GetAim()) + \
                           " #SHOT: " + str(self.agent.m_Threshold.GetShot() - _iShotNum) + " "
                self.send(msg)

                self.agent.m_iAmmo -= 1
                return True

        b = ShotBehaviour()
        self.add_behaviour(b)

    '''/**
     * Action to do when agent has an enemy at sight.
     *
     * This method is called when agent has looked and has found an enemy,
     * calculating (in agreement to the enemy position) the new direction where is aiming.
     *
     */'''
    def PerformAimAction(self):

        if self.m_AimedAgent is None:
            return

        if self.m_eTeam == self.m_AimedAgent.getTeam():
            print("OJO, mismo bando en PerformAimAction!")

        self.m_Movement.m_Destination.x = self.m_AimedAgent.m_Position.x
        self.m_Movement.m_Destination.y = self.m_AimedAgent.m_Position.y
        self.m_Movement.m_Destination.z = self.m_AimedAgent.m_Position.z
        self.m_Movement.CalculateNewOrientation()

    '''/**
     * To know if an enemy is aimed.
     *
     * This method is called just before agent can shoot.
     * If an enemy is aimed, a value of <tt> TRUE</tt> is returned. Otherwise, the return value is <tt> FALSE</tt>.
     * The result is used to decide if agent must shoot.
     *
     * @return <tt> TRUE</tt> (aimed enemy) | <tt> FALSE</tt> (no aimed enemy)
     *
     */'''
    def HaveAgentToShot(self):
        return self.m_AimedAgent != None

    # End of non-overloadable Methods

    # Methods to overload

    '''/**
     * Request for medicine.
     *
     * This method sends a <b> FIPA REQUEST </b> message to all agents who offers the <tt> m_sMedicService </tt> service.
     *
     * The content of message is: <tt> ( x , y , z ) ( health ) </tt>.
     *
     * Variable <tt> m_iMedicsCount </tt> is updated.
     *
     * <em> It's very useful to overload this method. </em>
     *
     */'''
    async def CallForMedic(self, behaviour):
        msg = Message()
        msg.set_metadata("performative", "get")
        msg.to = self.service_jid
        msg.body = self.MEDIC_SERVICE
        await behaviour.send(msg)
        result = await behaviour.receive(timeout=10000)

        if result:
            self.m_iMedicsCount = len(result)

            # Fill the REQUEST message
            msg = Message()
            msg.set_metadata("performative", "cfm")
            msg.body = " ( " + str(self.m_Movement.m_Position.x) + " , " + str(self.m_Movement.m_Position.y) + " , " +\
                       str(self.m_Movement.m_Position.z) + " ) ( " + str(self.m_iHealth) + " ) "

            for medic in result:
                msg.to = medic
                await behaviour.send(msg)

                print(self.name+ ": Need a Medic! (v21)")

        else:
            self.m_iMedicsCount = 0

    '''/**
     * Request for ammunition.
     *
     * This method sends a <b> FIPA REQUEST </b> message to all agents who offers the <tt> m_sAmmoService </tt> service.
     *
     * The content of message is: <tt> ( x , y , z ) ( ammo ) </tt>.
     *
     * Variable <tt> m_iFieldOpsCount </tt> is updated.
     *
     * <em> It's very useful to overload this method. </em>
     *
     */'''
    async def CallForAmmo(self, behaviour):
        msg = Message()
        msg.set_metadata("performative", "get")
        msg.to = self.service_jid
        msg.body = self.AMMO_SERVICE
        await behaviour.send(msg)
        result = await behaviour.receive(timeout=10000)

        if result:
            self.m_iFieldOpsCount = len(result)

            # Fill the REQUEST message
            msg = Message()
            msg.set_metadata("performative", "cfa")
            msg.body = " ( " + str(self.m_Movement.m_Position.x) + " , " + str(self.m_Movement.m_Position.y) + " , " +\
                       str(self.m_Movement.m_Position.z) + " ) ( " + str(self.m_iHealth) + " ) "

            for ammo in result:
                msg.to = ammo
                await behaviour.send(msg)

                print(self.name+ ": Need a Ammo! (v22)")

        else:
            self.m_iFieldOpsCount = 0

    '''/**
     * Request for backup.
     *
     * This method sends a <b> FIPA REQUEST </b> message to all agents who offers the <tt> m_sBackupService</tt> service.
     *
     * The content of message is: <tt> ( x , y , z ) ( SoldiersCount ) </tt>.
     *
     * Variable <tt> m_iSoldiersCount </tt> is updated.
     *
     * <em> It's very useful to overload this method. </em>
     *
     */'''
    async def CallForBackup(self, behaviour):

        msg = Message()
        msg.set_metadata("performative", "get")
        msg.to = self.service_jid
        msg.body = self.BACKUP_SERVICE
        await behaviour.send(msg)
        result = await behaviour.receive(timeout=10000)

        if result:
            self.m_iSoldiersCount = len(result)

            ## Fill the REQUEST message
            msg = Message()
            msg.set_metadata("performative", "cfb")
            msg.body = " ( " + str(self.m_Movement.m_Position.x) + " , " + str(self.m_Movement.m_Position.y) + " , " + \
                       str(self.m_Movement.m_Position.z) + " ) ( " + str(self.m_iHealth) + " ) "

            for backup in result.body:
                msg.to = backup
                await behaviour.send(msg)

                print(self.name + ": Need a Backup! (v32)")

        else:
            self.m_iSoldiersCount = 0

    '''/**
     * Update priority of all 'prepared (to execute)' tasks.
     *
     * This method is invoked in the state <em>STANDING</em>, and it's used to re-calculate the priority of all tasks (targets) int the task list
     * of the agent. The reason is because JGOMAS kernel always execute the highest priority task.
     *
     * <em> It's very useful to overload this method. </em>
     *
     */'''
    def UpdateTargets(self): pass

    '''/**
     * Should we update now all 'prepared (to execute)' tasks?
     *
     * This method is a decision function invoked in the state <em>GOTO_TARGET</em>. A value of <tt> TRUE</tt> break out the inner loop,
     * making possible to JGOMAS kernel extract the highest priority task, or update some attributes of the current task.
     * By default, the return value is <tt> FALSE</tt>, so we execute the current task until it finalizes.
     *
     * <em> It's very useful to overload this method. </em>
     *
     * @return <tt> FALSE</tt>
     *
     */'''
    def ShouldUpdateTargets(self): return False

    '''/**
     * The agent has got the objective pack.
     *
     * This method is called when this agent walks on the objective pack, getting it.
     *
     * <em> It's very useful to overload this method. </em>
     *
     */'''
    def ObjectivePackTaken(self): pass  # Should we do anything when we take the objective pack?

    '''/**
     * Definition of priorities for each kind of task.
     *
     * This method can be implemented in CBasicTroop's derived classes to define the task's priorities in agreement to
     * the role of the new class. Priorities must be defined in the array <tt> m_TaskPriority</tt>.
     *
     * <em> It's very useful to overload this method. </em>
     *
     */'''
    def SetUpPriorities(self): pass

    '''/**
     * Action to do if this agent cannot shoot.
     *
     * This method is called when the agent try to shoot, but has no ammo. The agent will spit enemies out. :-)
     *
     * <em> It's very useful to overload this method. </em>
     *
     */'''
    def PerformNoAmmoAction(self): pass

    '''/**
     * Action to do when this agent reaches the target of current task.
     *
     * This method is called when the agent goes to state <em>TARGET_REACHED</em>. In agreement to current task, agent must realize some actions
     * (for example, to get next point to walk from patrolling path). The actions in common to all roles are implemented at this level of hierarchy:
     * <em>TASK_PATROLLING</em>, <em>TASK_WALKING_PATH</em>, <em>TASK_RUN_AWAY</em>.
     *
     * <em> It's very useful to overload this method. </em>
     *
     * @param _CurrentTask
     *
     */'''
    def PerformTargetReached(self, _CurrentTask):

        sNewPosition = ""
        if _CurrentTask.m_iType == CTask.TASK_PATROLLING:
            self.m_iControlPointsIndex = self.m_iControlPointsIndex + 1
            if self.m_iControlPointsIndex >= len(self.m_ControlPoints):
                self.m_iControlPointsIndex = 0
            '''/*System.out.println("CP[" + m_iControlPointsIndex + "] = ( " +
                    m_ControlPoints[m_iControlPointsIndex].x + " , " +
                    m_ControlPoints[m_iControlPointsIndex].z + " )");*/'''
            sNewPosition = " ( " + str(self.m_ControlPoints[self.m_iControlPointsIndex].x) + " , " + \
                           str(self.m_ControlPoints[self.m_iControlPointsIndex].y) + " , " + \
                           str(self.m_ControlPoints[self.m_iControlPointsIndex].z) + " ) "
            self.AddTask(CTask.TASK_PATROLLING, self.name, sNewPosition)

        elif _CurrentTask.m_iType == CTask.TASK_WALKING_PATH:
            self.m_iAStarPathIndex = self.m_iAStarPathIndex + 1
            if self.m_iAStarPathIndex >= len(self.m_AStarPath):
                self.m_iAStarPathIndex = 0
                _CurrentTask.m_bErasable = True
            else:
                sNewPosition = " ( " + str(self.m_AStarPath[self.m_iAStarPathIndex].x) + " , " + \
                               str(self.m_AStarPath[self.m_iAStarPathIndex].y) + " , " + \
                               str(self.m_AStarPath[self.m_iAStarPathIndex].z) + " ) "
                self.AddTask(CTask.TASK_WALKING_PATH, self.name, sNewPosition)

        elif _CurrentTask.m_iType == CTask.TASK_RUN_AWAY:
            m_bEscaping = False

    '''/**
     * Calculates a new destiny position to escape.
     *
     * This method is called before the agent creates a task for escaping. It generates a valid random point in a radius of 50 units.
     * Once position is calculated, agent updates its destiny to the new position, and automatically calculates the new direction.
     *
     * <em> It's very useful to overload this method. </em>
     *
     */'''
    def GenerateEscapePosition(self):

        while True:
            self.m_Movement.CalculateNewDestination(50, 50)
            if self.CheckStaticPosition(self.m_Movement.m_Destination.x, self.m_Movement.m_Destination.z):
                self.m_Movement.CalculateNewOrientation()
                return

    '''
    Calculates a new destiny position to walk.

    This method is called before the agent creates a <tt> TASK_GOTO_POSITION</tt> task. It will try (for 5 attempts) to generate a
    valid random point in a radius of 20 units. If it doesn't generate a valid position in this cycle, it will try it in next cycle.
    Once a position is calculated, agent updates its destination to the new position, and automatically calculates the new direction.

    <em> It's very useful to overload this method. </em>

    @return <tt> TRUE</tt>: valid position generated / <tt> FALSE</tt> cannot generate a valid position

    '''
    def GeneratePath(self):
        print(self.name + " Current Position: " + str(self.m_Movement.m_Position.x) + ", " +
              str(self.m_Movement.m_Position.z))

        b_done = False
        for i_attempts in [1,2,3,4,5]:
            self.m_Movement.CalculateNewDestination(20,20)

            print (self.name + " New Position: " + str(self.m_Movement.m_Destination.x) + ", " + str(self.m_Movement.m_Destination.z))

            if self.CheckStaticPosition(self.m_Movement.m_Destination.x, self.m_Movement.m_Destination.z):
                # we must insert a task to go to a new position, so agent will follow previous path
                s_new_position = " ( " + str(self.m_Movement.m_Destination.x) + " , " + str(self.m_Movement.m_Destination.y) + " , " + str(self.m_Movement.m_Destination.z) + " ) "
                self.AddTask(CTask.TASK_GOTO_POSITION, self.name, s_new_position, self.m_CurrentTask.m_iPriority + 1)
                b_done = True
                break

        return b_done

    '''
    Calculates an array of positions for patrolling.

    When this method is called, it creates an array of <tt> n</tt> random positions. For medics and fieldops, the rank 
    of <tt> n</tt> is [1..1]. For soldiers, the rank of <tt> n</tt> is [5..10].

    <em> It's very useful to overload this method. </em>
    '''
    def CreateControlPoints(self):

        i_max_cp = 2
        i_radius = 2

        if self.m_eClass in [self.CLASS_MEDIC, self.CLASS_FIELDOPS]:
            i_max_cp = 3
            i_radius = 10

        elif self.m_eClass == self.CLASS_SOLDIER:
            i_max_cp = int(random.random() * 5) + 5
            i_radius = 50

        elif self.m_eClass in [self.CLASS_ENGINEER, self.CLASS_NONE]:
            pass

        self.m_ControlPoints = []  # Vector3D [iMaxCP]
        for i in range(0, i_max_cp-1):
            control_point = Vector3D()
            while True:
                x = self.m_Map.GetTargetX() + ((i_radius/2) - (random.random() * i_radius))
                z = self.m_Map.GetTargetZ() + ((i_radius/2) - (random.random() * i_radius))

                if self.CheckStaticPosition(x, z):
                    control_point.x = x
                    control_point.z = z
                    self.m_ControlPoints.append(control_point)
                    break

    '''
    Action to do when the agent tries to escape.

    This method is just called before this agent creates a <tt> TASK_RUN_AWAY</tt> task. By default, the only thing it 
    does is to reset its aimed enemy: <tt> m_AimedAgent = null</tt>. If it's overloaded, it's convenient to call 
    parent's method.

    <em> It's very useful to overload this method. </em>
    '''
    def PerformEscapeAction(self):
        self.m_AimedAgent = None

    '''
    Action to do when an agent is being shot.

    This method is called every time this agent receives a messager from agent Manager informing it is being shot.

    <em> It's very useful to overload this method. </em>
    '''
    def PerformInjuryAction(self):
        pass

    '''
    Action to do when ammo or health values exceed the threshold allowed.
     
    This method is called when current values of ammo and health exceed the threshold allowed. These values are checked
    by <tt> Launch_MedicAmmo_RequestBehaviour</tt> behaviour, every ten seconds. Perhaps it is convenient to create a
    <tt> TASK_RUN_AWAY</tt> task.

    <em> It's very useful to overload this method. </em>
    '''
    def PerformThresholdAction(self):
        pass

    '''
     Calculates if there is an enemy at sight.

     This method scans the list <tt> m_FOVObjects</tt> (objects in the Field Of View of the agent) looking for an enemy.
     If an enemy agent is found, a value of <tt> TRUE</tt> is returned and variable <tt> m_AimedAgent</tt> is updated.
     Note that there is no criterion (proximity, etc.) for the enemy found.
     Otherwise, the return value is <tt> FALSE</tt>.

     <em> It's very useful to overload this method. </em>
     
     @return <tt> TRUE</tt>: enemy found / <tt> FALSE</tt> enemy not found
     '''
    def GetAgentToAim(self):

        if not self.m_FOVObjects:
            self.m_AimedAgent = None
            return False

        for s in self.m_FOVObjects:
            if s.getType() >= CPack.PACK_NONE:
                continue

            eTeam = s.getTeam()

            if self.m_eTeam == eTeam:
                continue

            self.m_AimedAgent = s
            return True
        self.m_AimedAgent = None
        return False

    '''
    Action to do when the agent is looking at.
    
    This method is called just after Look method has ended.
    
    <em> It's very useful to overload this method. </em>
    '''
    def PerformLookAction(self):
        pass

    # End of Methods to overload

