import asyncio
import json
import random
import time

from loguru import logger

from spade.message import Message
from spade.behaviour import OneShotBehaviour, PeriodicBehaviour, FSMBehaviour, State, CyclicBehaviour
from spade.template import Template

from pygomas.ontology import TEAM_NONE, TEAM_ALLIED, TEAM_AXIS
from . import MIN_POWER, POWER_UNIT, MIN_STAMINA, STAMINA_UNIT, MIN_AMMO, MAX_AMMO, MAX_STAMINA, MAX_POWER, \
    MAX_HEALTH, MIN_HEALTH
from .ontology import MEDIC_SERVICE, AMMO_SERVICE, BACKUP_SERVICE, PERFORMATIVE, NAME, TYPE, TEAM, MAP, X, Y, Z, QTY, \
    ANGLE, DISTANCE, HEALTH, AIM, SHOTS, DEC_HEALTH, VEL_X, VEL_Y, VEL_Z, HEAD_X, HEAD_Y, HEAD_Z, AMMO, \
    PERFORMATIVE_OBJECTIVE, PERFORMATIVE_INIT, PERFORMATIVE_GAME, PERFORMATIVE_SHOT, PERFORMATIVE_DATA, \
    PERFORMATIVE_GET, PERFORMATIVE_CFM, PERFORMATIVE_CFA, PERFORMATIVE_CFB, FOV, PACKS, PERFORMATIVE_PACK_TAKEN
from .agent import AbstractAgent, LONG_RECEIVE_WAIT
from .threshold import Threshold
from .map import TerrainMap
from .mobile import Mobile
from .task import TASK_GET_OBJECTIVE, TASK_PATROLLING, TASK_WALKING_PATH, TASK_RUN_AWAY, TASK_GOTO_POSITION, \
    TaskManager, TASK_RETURN_TO_BASE
from .vector import Vector3D
from .sight import Sight
from .pack import PACK_MEDICPACK, PACK_AMMOPACK, PACK_OBJPACK, PACK_NONE
from .config import Config

DEFAULT_RADIUS = 20
ESCAPE_RADIUS = 50

PRECISION_Z = 0.5
PRECISION_X = 0.5

INTERVAL_TO_MOVE = 0.033
INTERVAL_TO_LOOK = 0.500

ARG_TEAM = 0

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


class Troop(AbstractAgent):

    def __init__(self, jid, passwd, team=TEAM_NONE, manager_jid="cmanager@localhost", service_jid="cservice@localhost"):

        self.task_manager = TaskManager()

        self.service_types = []

        # Variable used to store the AID of Manager
        self.manager = manager_jid
        self.service = service_jid

        # Variable indicating if this agent is carrying the objective pack (flag)
        self.is_objective_carried = False

        # Array of points used in patrolling task
        self.control_points = []

        # Current position in array m_ControlPoints
        self.control_points_index = 0

        # Array of points used in walking (a calculated) path task
        self.a_star_path = []

        # Current position in array AStarPath
        self.a_star_path_index = 0

        # List of objects in the agent's Field Of Vision
        self.fov_objects = []

        # Current aimed enemy
        self.aimed_agent = None  # Sight

        self.eclass = 0
        self.health = 0
        self.protection = 0
        self.stamina = 0
        self.power = 0
        self.ammo = 0

        # Variable indicating if agent is fighting at this moment
        self.is_fighting = False

        # Variable indicating if agent is escaping at this moment
        self.is_escaping = False

        # Current position, direction, and so on...
        self.movement = None  # CMobile

        self.soldiers_count = 0
        self.medics_count = 0
        self.engineers_count = 0
        self.fieldops_count = 0
        self.team_count = 0

        # Limits of some variables (to trigger some events)
        self.threshold = Threshold()

        # Current Map
        self.map = None  # TerrainMap

        self.fsm_behaviour = None  # FSMBehaviour

        super().__init__(jid, passwd, team=team, service_jid=service_jid)

    def start(self, auto_register=True):
        self.health = MAX_HEALTH
        self.protection = 25
        self.stamina = MAX_STAMINA
        self.power = MAX_POWER
        self.ammo = MAX_AMMO

        # Send a welcome message, and wait for the beginning of match
        self.add_behaviour(self.CreateBasicTroopBehaviour())

        # Behaviour to get the objective of the game, to create the corresponding task
        t = Template()
        t.set_metadata(PERFORMATIVE, PERFORMATIVE_OBJECTIVE)
        self.add_behaviour(self.ObjectiveBehaviour(), t)

        t = Template()
        t.set_metadata(PERFORMATIVE, PERFORMATIVE_INIT)
        self.add_behaviour(self.InitResponderBehaviour(), t)

        # Behaviour to listen to manager if game has finished
        t = Template()
        t.set_metadata(PERFORMATIVE, PERFORMATIVE_GAME)
        self.add_behaviour(self.GameFinishedBehaviour(), t)

        # Behaviour to handle Pack Taken messages
        t = Template()
        t.set_metadata(PERFORMATIVE, PERFORMATIVE_PACK_TAKEN)
        self.add_behaviour(self.PackTakenBehaviour(), t)

        # Behaviour to handle Shot messages
        t = Template()
        t.set_metadata(PERFORMATIVE, PERFORMATIVE_SHOT)
        self.add_behaviour(self.ShotBehaviour(period=0), t)

        # Behaviour to inform manager our position, status, and so on
        t = Template()
        t.set_metadata(PERFORMATIVE, PERFORMATIVE_DATA)
        self.add_behaviour(self.DataFromTroopBehaviour(period=0.3), t)

        # Behaviour to increment inner variables (Power, Stamina and Health Bars)
        # self.agent.Launch_BarsAddOn_InnerBehaviour()
        self.add_behaviour(self.RestoreBehaviour(period=1))

        # Behaviour to call for medics or fieldops
        t = Template()
        t.set_metadata(PERFORMATIVE, PERFORMATIVE_GET)
        self.add_behaviour(self.MedicAmmoRequestBehaviour(period=1), t)

        future = super().start(auto_register)
        return future

    class CreateBasicTroopBehaviour(OneShotBehaviour):
        async def run(self):
            if self.agent.service_types is not None:
                for service in self.agent.service_types:
                    self.agent.register_service(str(service))

            msg = Message(to=self.agent.manager)
            msg.set_metadata(PERFORMATIVE, PERFORMATIVE_INIT)
            msg.body = json.dumps({NAME: self.agent.name, TYPE: str(self.agent.eclass), TEAM: str(self.agent.team)})
            await self.send(msg)

    class InitResponderBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=LONG_RECEIVE_WAIT)
            if msg:
                map_name = json.loads(msg.body)[MAP]
                logger.info("[" + self.agent.name + "]: Beginning to fight")
                self.agent.map = TerrainMap()
                config = Config()
                self.agent.map.load_map(map_name, config)
                self.agent.movement = Mobile()
                self.agent.movement.set_size(self.agent.map.get_size_x(), self.agent.map.get_size_z())

                self.agent.generate_spawn_position()
                self.agent.setup_priorities()

                # Behaviour to launch the FSM
                self.agent.launch_fsm_behaviour()

                self.kill()

    # Behaviour to get the objective of the game, to create the corresponding task
    class ObjectiveBehaviour(CyclicBehaviour):
        async def run(self):
            logger.info("{} waiting for objective.".format(self.agent.name))
            msg = await self.receive(timeout=LONG_RECEIVE_WAIT)
            if msg:
                content = json.loads(msg.body)
                if self.agent.team == TEAM_ALLIED:
                    self.agent.task_manager.add_task(TASK_GET_OBJECTIVE, self.agent.name, content)
                    logger.info("Allied {} has its objective at {}".format(self.agent.name, content))
                elif self.agent.team == TEAM_AXIS:
                    self.agent.create_control_points()
                    new_position = {X: self.agent.control_points[0].x,
                                    Y: self.agent.control_points[0].y,
                                    Z: self.agent.control_points[0].z}
                    self.agent.task_manager.add_task(TASK_PATROLLING, self.agent.name, new_position)
                    logger.info("Axis {} has its objective at {}".format(self.agent.name, str(new_position)))
                self.kill()

    # Behaviour to listen to manager if game has finished
    class GameFinishedBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=LONG_RECEIVE_WAIT)
            if msg:
                logger.info("[" + self.agent.name + "]: Bye!")
                self.kill()
                await self.agent.die()

    # Behaviour to handle Pack Taken messages
    class PackTakenBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=LONG_RECEIVE_WAIT)
            if msg:
                # Agent has stepped on pack
                content = json.loads(msg.body)
                logger.info("{} got pack {}:".format(self.agent.name, content))
                pack_type = int(content[TYPE])
                quantity = int(content[QTY])

                self.agent.pack_taken(pack_type, quantity)

    # Behaviour to handle Shot messages
    class ShotBehaviour(PeriodicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=LONG_RECEIVE_WAIT)
            if msg:
                content = json.loads(msg.body)
                decrease_health = int(content[DEC_HEALTH])

                self.agent.decrease_health(decrease_health)
                logger.info("Agent {} has been hit by a shot! Loses {} health points ({})."
                            .format(self.agent.name, decrease_health, self.agent.health))

                if self.agent.health <= 0:
                    logger.info(self.agent.name + ": DEAD!!")
                    self.agent.task_manager.clear()
                    if self.agent.is_objective_carried:
                        self.agent.is_objective_carried = False
                    await self.agent.die()

                self.agent.perform_injury_action()

    # Behaviour to inform JGomasManager our position, status, and so on
    class DataFromTroopBehaviour(PeriodicBehaviour):
        async def run(self):
            if not self.agent.movement:
                return
            content = {NAME: self.agent.name,
                       X: self.agent.movement.position.x,
                       Y: self.agent.movement.position.y,
                       Z: self.agent.movement.position.z,
                       VEL_X: self.agent.movement.velocity.x,
                       VEL_Y: self.agent.movement.velocity.y,
                       VEL_Z: self.agent.movement.velocity.z,
                       HEAD_X: self.agent.movement.heading.x,
                       HEAD_Y: self.agent.movement.heading.y,
                       HEAD_Z: self.agent.movement.heading.z,
                       HEALTH: self.agent.health,
                       AMMO: self.agent.ammo}
            msg = Message(to=self.agent.manager)
            msg.set_metadata(PERFORMATIVE, PERFORMATIVE_DATA)
            msg.body = json.dumps(content)
            await self.send(msg)

            info = await self.receive(LONG_RECEIVE_WAIT)
            if info is None:
                return
            info = json.loads(info.body)

            packs = info[PACKS] if info[PACKS] is not None else []
            for pack in packs:
                pack = json.loads(pack)
                quantity = pack[QTY]
                type_ = pack[TYPE]
                self.agent.pack_taken(pack_type=type_, quantity=quantity)

            self.agent.fov_objects = []
            fovs = info[FOV] if info[FOV] is not None else []
            if len(fovs) <= 0:
                self.agent.aimed_agent = None
            else:
                for idx, obj in enumerate(fovs):
                    s = Sight()
                    s.sight_id = idx
                    s.team = int(obj[TEAM])
                    s.type = int(obj[TYPE])
                    s.angle = float(obj[ANGLE])
                    s.distance = float(obj[DISTANCE])
                    s.health = int(obj[HEALTH])
                    s.position.x = float(obj[X])
                    s.position.y = float(obj[Y])
                    s.position.z = float(obj[Z])
                    self.agent.fov_objects.append(s)

    # Behaviour to increment inner variables (Power, Stamina and Health Bars)
    class RestoreBehaviour(PeriodicBehaviour):
        async def run(self):
            if self.agent.stamina < MAX_STAMINA:
                self.agent.stamina = self.agent.stamina + 1

            if self.agent.power < MAX_POWER:
                self.agent.power = self.agent.power + 1

            if self.agent.eclass == CLASS_MEDIC and self.agent.health > MIN_HEALTH:
                if self.agent.health < MAX_HEALTH:
                    self.agent.health = self.agent.health + 1

    # Behaviour to call for medics or fieldops
    class MedicAmmoRequestBehaviour(PeriodicBehaviour):
        async def run(self):
            low_level = False
            if self.agent.health < self.agent.threshold.get_health():
                low_level = True
                await self.agent.call_for_medic(self)

            if self.agent.ammo < self.agent.threshold.get_ammo():
                low_level = True
                await self.agent.call_for_ammo(self)

            if low_level:
                await self.agent.perform_threshold_action()

    # Behaviour to launch the FSM
    def launch_fsm_behaviour(self):

        # FSM Declaration
        self.fsm_behaviour = FSMBehaviour()

        # Register state STATE_STANDING (first state)
        self.fsm_behaviour.add_state(STATE_STANDING, self.StandingState(), initial=True)

        # Register state STATE_GOTO_TARGET
        self.fsm_behaviour.add_state(STATE_GOTO_TARGET, self.GoToTargetState())

        # Register state STATE_TARGET_REACHED
        self.fsm_behaviour.add_state(STATE_TARGET_REACHED, self.TargetReachedState())

        # Register state STATE_FIGHTING
        self.fsm_behaviour.add_state(STATE_FIGHTING, self.FightingState())

        # Register state STATE_QUIT (final state)
        self.fsm_behaviour.add_state(STATE_QUIT, self.QuitState())

        # Register the transitions
        # m_FSM.registerDefaultTransition(STATE_STANDING, STATE_QUIT);
        # self.m_FSM.registerDefaultTransition(self.STATE_STANDING, self.STATE_STANDING) ## OJO
        self.fsm_behaviour.add_transition(STATE_STANDING, STATE_STANDING)
        self.fsm_behaviour.add_transition(STATE_STANDING, STATE_GOTO_TARGET)
        self.fsm_behaviour.add_transition(STATE_STANDING, STATE_QUIT)

        # self.m_FSM.registerDefaultTransition(self.STATE_GOTO_TARGET, self.STATE_GOTO_TARGET)
        self.fsm_behaviour.add_transition(STATE_GOTO_TARGET, STATE_GOTO_TARGET)
        self.fsm_behaviour.add_transition(STATE_GOTO_TARGET, STATE_STANDING)
        self.fsm_behaviour.add_transition(STATE_GOTO_TARGET, STATE_TARGET_REACHED)
        self.fsm_behaviour.add_transition(STATE_GOTO_TARGET, STATE_FIGHTING)

        # self.m_FSM.registerDefaultTransition(self.STATE_TARGET_REACHED, self.STATE_STANDING)
        self.fsm_behaviour.add_transition(STATE_TARGET_REACHED, STATE_STANDING)
        self.fsm_behaviour.add_transition(STATE_TARGET_REACHED, STATE_STANDING)

        # self.m_FSM.registerDefaultTransition(self.STATE_FIGHTING, self.STATE_FIGHTING)
        self.fsm_behaviour.add_transition(STATE_FIGHTING, STATE_FIGHTING)
        self.fsm_behaviour.add_transition(STATE_FIGHTING, STATE_STANDING)

        # launching the FSM
        self.add_behaviour(self.fsm_behaviour)

    def generate_spawn_position(self):

        if self.team == TEAM_ALLIED:
            w = self.map.allied_base.end.x - self.map.allied_base.init.x
            h = self.map.allied_base.end.z - self.map.allied_base.init.z
            offset_x = self.map.allied_base.init.x
            offset_z = self.map.allied_base.init.z

        else:
            w = self.map.axis_base.end.x - self.map.axis_base.init.x
            h = self.map.axis_base.end.z - self.map.axis_base.init.z
            offset_x = self.map.axis_base.init.x
            offset_z = self.map.axis_base.init.z

        x = int((random.random() * w) + offset_x)
        z = int((random.random() * h) + offset_z)

        logger.info("Spawn position for agent {} is ({}, {})".format(self.name, x, z))

        self.movement.position.x = x
        self.movement.position.y = 0
        self.movement.position.z = z

    def move(self, dt):
        original_position = Vector3D()
        original_position.x = self.movement.position.x
        original_position.y = self.movement.position.y
        original_position.z = self.movement.position.z

        if self.movement.calculate_position(dt):
            if not self.check_static_position():
                logger.info(self.name + ": Can't walk to {}. I stay at {}".format(self.movement.position,
                                                                                  original_position))
                self.movement.position.x = original_position.x
                self.movement.position.y = original_position.y
                self.movement.position.z = original_position.z
                return MV_CANNOT_GET_POSITION
            return MV_OK
        return MV_NOT_MOVED_BY_TIME

    # Behaviours to handle our FSM
    class StandingState(State):
        async def run(self):
            num_tasks = len(self.agent.task_manager)
            if num_tasks <= 0:
                self.set_next_state(STATE_STANDING)
                logger.info(self.agent.name + ": Behaviour ............ NO TASKS!!!")
                await asyncio.sleep(1.0)
                return

            if self.agent.health <= 0:
                self.agent.task_manager.clear()
                self.set_next_state(STATE_QUIT)  # if we have nothing to do, go to QUIT state

                return

            self.agent.update_targets()

            self.agent.task_manager.select_highest_priority_task()
            logger.info(self.agent.name + ": select task with priority {}".
                        format(self.agent.task_manager.get_current_task()))

            self.agent.movement.destination.x = self.agent.task_manager.get_current_task().position.x
            self.agent.movement.destination.y = self.agent.task_manager.get_current_task().position.y
            self.agent.movement.destination.z = self.agent.task_manager.get_current_task().position.z

            self.agent.movement.calculate_new_orientation()
            self.set_next_state(STATE_GOTO_TARGET)

            return

    class QuitState(State):
        async def run(self):
            logger.info(self.agent.name + ": Behaviour ............ [QUIT]")
            await self.agent.die()
            return

    class GoToTargetState(State):

        def __init__(self):
            self.is_initializated = False
            super().__init__()

        async def run(self):
            if not self.is_initializated:
                self.agent.last_time_move = self.agent.last_time_look = time.time()
                self.is_initializated = True

            self.set_next_state(STATE_GOTO_TARGET)  # GOTO_TARGET

            current_time = time.time()
            dt = current_time - self.agent.last_time_look
            if dt > INTERVAL_TO_LOOK:
                self.agent.last_time_look = current_time
                # await self.agent.look()
                self.agent.perform_look_action()
                self.agent.get_agent_to_aim()
                if self.agent.have_agent_to_shot():
                    current_destination = self.agent.movement.destination
                    self.agent.perform_aim_action()
                    if not self.agent.shot(0):
                        self.agent.perform_no_ammo_action()
                    self.agent.movement.destination = current_destination
                    self.agent.last_time_move = current_time
                    return

            dt = current_time - self.agent.last_time_move
            if dt < INTERVAL_TO_MOVE:
                return
            self.agent.last_time_move = current_time

            move_result = self.agent.move(dt)

            if move_result == MV_OK:
                absx = abs(self.agent.movement.destination.x - self.agent.movement.position.x)
                absz = abs(self.agent.movement.destination.z - self.agent.movement.position.z)
                if (absx < PRECISION_X) and (absz < PRECISION_Z):
                    self.agent.movement.position.x = self.agent.movement.destination.x
                    self.agent.movement.position.z = self.agent.movement.destination.z
                    self.set_next_state(STATE_TARGET_REACHED)
                else:
                    if self.agent.should_update_targets():
                        self.set_next_state(STATE_STANDING)

            elif move_result == MV_CANNOT_GET_POSITION:
                if self.agent.generate_path():
                    self.set_next_state(STATE_STANDING)

            elif move_result == MV_NOT_MOVED_BY_TIME:
                pass

            return

    class TargetReachedState(State):

        async def run(self):
            logger.success(self.agent.name + ": Behaviour ............ [TARGET REACHED]")
            logger.trace("position: {} destination: {}"
                         .format(self.agent.movement.position, self.agent.movement.destination))

            task = self.agent.task_manager.get_current_task()

            #if self.agent.task_manager.get_current_task().is_erasable:
            logger.info("Deleting task: {}".format(task))
            self.agent.task_manager.delete(task)

            self.agent.perform_target_reached(task)

            self.set_next_state(STATE_STANDING)

            return

    class FightingState(State):

        async def run(self):
            logger.info(self.agent.name + ": Behaviour ............ [FIGHTING]")
            self.set_next_state(STATE_FIGHTING)
            await asyncio.sleep(0.5)
            return

    # Non-overloadable Methods, interesting for user

    def pack_taken(self, pack_type, quantity):
        if pack_type == PACK_MEDICPACK:
            self.increase_health(quantity)
        elif pack_type == PACK_AMMOPACK:
            self.increase_ammo(quantity)
        elif pack_type == PACK_OBJPACK:
            self.objective_pack_taken()
            if self.team == TEAM_ALLIED:
                self.is_objective_carried = True
                x = ((self.map.allied_base.get_end_x() -
                      self.map.allied_base.get_init_x()) / 2) + \
                    self.map.allied_base.get_init_x()
                y = ((self.map.allied_base.get_end_y() -
                      self.map.allied_base.get_init_y()) / 2) + \
                    self.map.allied_base.get_init_y()
                z = ((self.map.allied_base.get_end_z() -
                      self.map.allied_base.get_init_z()) / 2) + \
                    self.map.allied_base.get_init_z()
                new_position = {X: x, Y: y, Z: z}
                self.task_manager.add_task(TASK_RETURN_TO_BASE, self.name, new_position)

    def get_health(self):
        """
         Get the current health of the agent.

         :returns current value for health
         :rtype int
         """
        return self.health

    def increase_health(self, quantity):
        """
        Increments the current health of the agent.

        :param quantity: positive quantity to increment
        """
        self.health += quantity
        if self.health > MAX_HEALTH:
            self.health = MAX_HEALTH

    def decrease_health(self, quantity):
        """
        Decrements the current health of the agent.

        :param quantity: negative quantity to decrement
        """
        self.health -= quantity
        if self.health < MIN_HEALTH:
            self.health = MIN_HEALTH

    def get_ammo(self):
        """
        Get the current ammunition of the agent.

        :returns: current value for ammo
        """
        return self.ammo

    def increase_ammo(self, quantity):
        """
        Increments the current ammunition of the agent.

        :param quantity: positive quantity to increment
        """
        self.ammo += quantity
        if self.ammo > MAX_AMMO:
            self.ammo = MAX_AMMO

    def decrease_ammo(self, quantity):
        """
        Decrements the current ammunition of the agent.

        :param quantity: negative quantity to decrement
        """
        self.ammo -= quantity
        if self.ammo < MIN_AMMO:
            self.ammo = MIN_AMMO

    def get_stamina(self):
        """
        Get the current stamina of the agent.

        :returns: current value for stamina bar
        """
        return self.stamina

    def use_stamina(self):
        """
        Use stamina from the stamina bar if possible (there is at least 5 units).
        """
        self.stamina -= STAMINA_UNIT
        if self.stamina <= MIN_STAMINA:
            self.stamina = MIN_STAMINA

    def get_power(self):
        """
        Get the current power of the agent.

        :returns: current value for power bar
        """
        return self.power

    def use_power(self):
        """
        Use power from the power bar if possible (there is at least 25 units).

        Power bar is reduced in 25 units.
        """
        self.power -= POWER_UNIT
        if self.power <= MIN_POWER:
            self.power = MIN_POWER

    def add_service_type(self, service_list):
        """
        Adds a type of service to the service type list.

        This method registers all types of services to offer in a list, excluding repeated services.

        :param service_list
        """

        if not self.service_types:
            self.service_types = []

        if service_list.lower() not in self.service_types:
            self.service_types.append(service_list.lower())

    def check_static_position(self, x=None, z=None):
        """
        Checks a position on the static map.

        This method checks if a position on the static map is valid to walk on, and returns the result.

        :param x:
        :param z:
        :returns True (agent can walk on) | False (agent cannot walk on)
        :rtype bool
        """
        if x is None:
            x = self.movement.position.x
        if z is None:
            z = self.movement.position.z

        x = int(x)
        z = int(z)
        return self.map.can_walk(x, z)

    def shot(self, shot_num):
        """
         The agent shoots in the direction which he is aiming.

         This method sends a FIPA INFORM message to Manager.
         Once message is sent, the variable ammo is decremented.

         :param shot_num: number of extra shots
         :type shot_num: int
         :returns True (shot done) | False (cannot shoot, has no ammo)
         :rtype bool
         """

        class ShotBehaviour(OneShotBehaviour):
            async def run(self):
                if self.agent.ammo <= MIN_AMMO:
                    return False

                if self.agent.aimed_agent is None:
                    logger.warning(self.agent.name + ": tried to shot to nobody")
                    return False

                # Fill the REQUEST message
                msg = Message()
                msg.to = self.agent.manager
                msg.set_metadata(PERFORMATIVE, PERFORMATIVE_SHOT)
                content = {NAME: self.agent.name, AIM: self.agent.threshold.get_aim(),
                           SHOTS: self.agent.threshold.get_shot() - shot_num}
                logger.info("Shot! {}".format(content))
                msg.body = json.dumps(content)
                await self.send(msg)

                self.agent.ammo -= 1
                return True

        b = ShotBehaviour()
        self.add_behaviour(b)

    def perform_aim_action(self):
        """
         Action to do when agent has an enemy at sight.

         This method is called when agent has looked and has found an enemy,
         calculating (in agreement to the enemy position) the new direction where is aiming.
         """

        if self.aimed_agent is None:
            return

        if self.team == self.aimed_agent.get_team():
            logger.warning("Same team in PerformAimAction!")

        self.movement.destination.x = self.aimed_agent.position.x
        self.movement.destination.y = self.aimed_agent.position.y
        self.movement.destination.z = self.aimed_agent.position.z
        self.movement.calculate_new_orientation()

    def have_agent_to_shot(self):
        """
        To know if an enemy is aimed.

        This method is called just before agent can shoot.
        If an enemy is aimed, a value of <tt> TRUE</tt> is returned. Otherwise, the return value is <tt> FALSE</tt>.
        The result is used to decide if agent must shoot.

        :returns True(aimed enemy) | False (no aimed enemy)
        :rtype bool
        """
        return self.aimed_agent is not None

    # End of non-overloadable Methods

    # Methods to overload

    async def call_for_medic(self, behaviour):
        """
        Request for medicine.

        This method sends a FIPA REQUEST message to all agents who offers the Medic service.

        The content of message is: {X: x ,Y:  y , Z: z, HEALTH: health}.

        Variable medics_count is updated.
        It's very useful to overload this method.
        """
        msg = Message()
        msg.set_metadata(PERFORMATIVE, PERFORMATIVE_GET)
        msg.to = self.service_jid
        msg.body = json.dumps({NAME: MEDIC_SERVICE, TEAM: self.team})
        await behaviour.send(msg)
        result = await behaviour.receive(timeout=LONG_RECEIVE_WAIT)

        if result:
            result = json.loads(result.body)
            self.medics_count = len(result)

            logger.info("{} got {} medics: {}".format(self.name, self.medics_count, result))

            # Fill the REQUEST message
            msg = Message()
            msg.set_metadata(PERFORMATIVE, PERFORMATIVE_CFM)
            msg.body = json.dumps({X: self.movement.position.x,
                                   Y: self.movement.position.y,
                                   Z: self.movement.position.z,
                                   HEALTH: self.health})

            for medic in result:
                msg.to = medic
                await behaviour.send(msg)

                logger.info("{}: Need a Medic! {}".format(self.name, msg))

        else:
            self.medics_count = 0

    async def call_for_ammo(self, behaviour):
        """
        Request for ammunition.

        This method sends a FIPA REQUEST message to all agents who offers the ammo_service service.

        The content of message is: {X: x ,Y:  y , Z: z, HEALTH: health}.

        Variable fieldOps_count is updated.

        It's very useful to overload this method.
        """
        msg = Message()
        msg.set_metadata(PERFORMATIVE, PERFORMATIVE_GET)
        msg.to = self.service_jid
        msg.body = json.dumps({NAME: AMMO_SERVICE, TEAM: self.team})
        await behaviour.send(msg)
        result = await behaviour.receive(timeout=LONG_RECEIVE_WAIT)

        if result:
            result = json.loads(result.body)
            self.fieldops_count = len(result)

            # Fill the REQUEST message
            msg = Message()
            msg.set_metadata(PERFORMATIVE, PERFORMATIVE_CFA)
            msg.body = json.dumps({X: self.movement.position.x,
                                   Y: self.movement.position.y,
                                   Z: self.movement.position.z,
                                   HEALTH: self.health})

            for ammo in result:
                msg.to = ammo
                await behaviour.send(msg)

                logger.info(self.name + ": Need a Ammo!")

        else:
            self.fieldops_count = 0

    async def call_for_backup(self, behaviour):
        """
        Request for backup.

        This method sends a FIPA REQUEST message to all agents who offers the backup_service service.

        The content of message is: {X: x ,Y:  y , Z: z, HEALTH: health}.

        Variable soldiers_count is updated.

        It's very useful to overload this method.
        """

        msg = Message()
        msg.set_metadata(PERFORMATIVE, PERFORMATIVE_GET)
        msg.to = self.service_jid
        msg.body = BACKUP_SERVICE
        await behaviour.send(msg)
        result = await behaviour.receive(timeout=LONG_RECEIVE_WAIT)

        if result:
            result = json.loads(result.body)
            self.soldiers_count = len(result)

            # Fill the REQUEST message
            msg = Message()
            msg.set_metadata(PERFORMATIVE, PERFORMATIVE_CFB)
            msg.body = json.dumps({X: self.movement.position.x,
                                   Y: self.movement.position.y,
                                   Z: self.movement.position.z,
                                   HEALTH: self.health})

            for backup in result.body:
                msg.to = backup
                await behaviour.send(msg)

                logger.info(self.name + ": Need a Backup!")

        else:
            self.soldiers_count = 0

    def update_targets(self):
        """
        Update priority of all 'prepared (to execute)' tasks.

        This method is invoked in the state STANDING, and it's used to re-calculate the priority of all tasks (targets) int the task list
        of the agent. The reason is because pyGOMAS kernel always execute the highest priority task.

        It's very useful to overload this method.
        """
        pass

    def should_update_targets(self):
        """
        Should we update now all 'prepared (to execute)' tasks?

        This method is a decision function invoked in the state GOTO_TARGET. A value of True break out the inner loop,
        making possible to pyGOMAS kernel extract the highest priority task, or update some attributes of the current task.
        By default, the return value is False, so we execute the current task until it finalizes.

        It's very useful to overload this method.

        :returns False
        :rtype: bool
        """
        return False

    def objective_pack_taken(self):
        """
        The agent has got the objective pack.

        This method is called when this agent walks on the objective pack, getting it.

        It's very useful to overload this method.
        """
        pass  # Should we do anything when we take the objective pack?

    def setup_priorities(self):
        """
        Definition of priorities for each kind of task.

        This method can be implemented in basic Troop's derived classes to define the task's priorities in agreement to
        the role of the new class. Priorities must be defined in the array task_priority.

        It's very useful to overload this method.
        """
        pass

    def perform_no_ammo_action(self):
        """
        Action to do if this agent cannot shoot.

        This method is called when the agent try to shoot, but has no ammo. The agent will spit enemies out. :-)

        It's very useful to overload this method.
        """
        pass

    def perform_target_reached(self, current_task):
        """
        Action to do when this agent reaches the target of current task.

        This method is called when the agent goes to state TARGET_REACHED. In agreement to current task, agent must realize some actions
        (for example, to get next point to walk from patrolling path). The actions in common to all roles are implemented at this level of hierarchy:
        TASK_PATROLLING, TASK_WALKING_PATH, TASK_RUN_AWAY.

        It's very useful to overload this method.

        :param current_task
        """

        if current_task.type == TASK_PATROLLING:
            self.control_points_index += 1
            if self.control_points_index >= len(self.control_points):
                self.control_points_index = 0
            new_position = {X: self.control_points[self.control_points_index].x,
                            Y: self.control_points[self.control_points_index].y,
                            Z: self.control_points[self.control_points_index].z}
            self.task_manager.add_task(TASK_PATROLLING, self.name, new_position)

        elif current_task.type == TASK_WALKING_PATH:
            self.a_star_path_index += 1
            if self.a_star_path_index >= len(self.a_star_path):
                self.a_star_path_index = 0
                current_task.is_erasable = True
            else:
                new_position = {X: self.a_star_path[self.a_star_path_index].x,
                                Y: self.a_star_path[self.a_star_path_index].y,
                                Z: self.a_star_path[self.a_star_path_index].z}
                self.task_manager.add_task(TASK_WALKING_PATH, self.name, new_position)

        elif current_task.type == TASK_RUN_AWAY:
            self.is_escaping = False

    def generate_escape_position(self):
        """
        Calculates a new destiny position to escape.
        This method is called before the agent creates a task for escaping. It generates a valid random point in a radius of 50 units.
        Once position is calculated, agent updates its destiny to the new position, and automatically calculates the new direction.

        It's very useful to overload this method. </em>
        """

        while True:
            self.movement.calculate_new_destination(radius_x=ESCAPE_RADIUS, radius_y=ESCAPE_RADIUS)
            if self.check_static_position(self.movement.destination.x, self.movement.destination.z):
                self.movement.calculate_new_orientation()
                return

    def generate_path(self):
        """
        Calculates a new destiny position to walk.

        This method is called before the agent creates a TASK_GOTO_POSITION task. It will try (for 5 attempts) to generate a
        valid random point in a radius of 20 units. If it doesn't generate a valid position in this cycle, it will try it in next cycle.
        Once a position is calculated, agent updates its destination to the new position, and automatically calculates the new direction.

        It's very useful to overload this method.

        :returns True: valid position generated / False: cannot generate a valid position
        """
        logger.info(f"{self.name} Current Position: {self.movement.position.x}, {self.movement.position.z}")

        is_done = False
        for _ in range(5):
            self.movement.calculate_new_destination(radius_x=DEFAULT_RADIUS, radius_y=DEFAULT_RADIUS)
            logger.info(f"{self.name} New Position: {self.movement.destination.x}, {self.movement.destination.z}")

            if self.check_static_position(self.movement.destination.x, self.movement.destination.z):
                # we must insert a task to go to a new position, so agent will follow previous path
                new_position = {X: self.movement.destination.x,
                                Y: self.movement.destination.y,
                                Z: self.movement.destination.z}
                self.task_manager.add_task(TASK_GOTO_POSITION, self.name, new_position,
                                           self.task_manager.get_current_task().priority + 1)
                is_done = True
                break

        return is_done

    def create_control_points(self):
        """
        Calculates an array of positions for patrolling.

        When this method is called, it creates an array of n random positions. For medics and fieldops, the rank
        of  n is [1..1]. For soldiers, the rank of n is [5..10].

        It's very useful to overload this method.
        """

        max_control_points = 2
        radius = 2

        if self.eclass in [CLASS_MEDIC, CLASS_FIELDOPS]:
            max_control_points = 3
            radius = 10

        elif self.eclass == CLASS_SOLDIER:
            max_control_points = int(random.random() * 5) + 5
            radius = 50

        elif self.eclass in [CLASS_ENGINEER, CLASS_NONE]:
            pass

        self.control_points = []  # Vector3D [iMaxCP]
        for i in range(max_control_points):
            control_point = Vector3D()
            while True:
                x = self.map.get_target_x() + ((radius / 2) - (random.random() * radius))
                x = max(0, x)
                x = int(min(self.map.size_x - 1, x))
                z = self.map.get_target_z() + ((radius / 2) - (random.random() * radius))
                z = max(0, z)
                z = int(min(self.map.size_z - 1, z))

                if self.check_static_position(x, z):
                    control_point.x = x
                    control_point.z = z
                    self.control_points.append(control_point)
                    break

            logger.success("Control point generated {}".format(control_point))

    def perform_escape_action(self):
        """
        Action to do when the agent tries to escape.

        This method is just called before this agent creates a TASK_RUN_AWAY task. By default, the only thing it
        does is to reset its aimed enemy: aimed_agent = null. If it's overloaded, it's convenient to call
        parent's method.

        It's very useful to overload this method.
        """
        self.aimed_agent = None

    def perform_injury_action(self):
        """
        Action to do when an agent is being shot.

        This method is called every time this agent receives a messager from agent Manager informing it is being shot.

        It's very useful to overload this method.
        """
        pass

    async def perform_threshold_action(self):
        """
        Action to do when ammo or health values exceed the threshold allowed.

        This method is called when current values of ammo and health exceed the threshold allowed. These values are checked
        by Launch_MedicAmmo_RequestBehaviour behaviour, every ten seconds. Perhaps it is convenient to create a
        TASK_RUN_AWAY task.

        It's very useful to overload this method.
        """
        pass

    def get_agent_to_aim(self):
        """
        Calculates if there is an enemy at sight.

        This method scans the list fov_objects (objects in the Field Of View of the agent) looking for an enemy.
        If an enemy agent is found, a value of True is returned and variable aimed_agent is updated.
        Note that there is no criterion (proximity, etc.) for the enemy found.
        Otherwise, the return value is False.

        It's very useful to overload this method.

        :returns True: enemy found / False: enemy not found
        """

        if not self.fov_objects:
            self.aimed_agent = None
            return False

        for tracked_object in self.fov_objects:
            if tracked_object.get_type() >= PACK_NONE:
                continue

            if self.team == tracked_object.get_team():
                continue

            self.aimed_agent = tracked_object
            return True
        self.aimed_agent = None
        return False

    def perform_look_action(self):
        """
        Action to do when the agent is looking at.

        This method is called just after Look method has ended.

        It's very useful to overload this method.
        """
        pass

    # End of Methods to overload
