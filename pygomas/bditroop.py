from spade_bdi.bdi import BDIAgent
import pyson
import datetime
from collections import deque

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
from .ontology import DESTINATION,POSITION,HEADING,VELOCITY,THRESHOLD_HEALTH,THRESHOLD_AMMO,THRESHOLD_AIM,THRESHOLD_SHOTS,MY_MEDICS,BASE,FLAG,PRECISION_Z,PRECISION_X,CONTROL_POINTS, MEDIC_SERVICE, AMMO_SERVICE, BACKUP_SERVICE, PERFORMATIVE, NAME, TYPE, TEAM, MAP, X, Y, Z, QTY, \
	ANGLE, DISTANCE, HEALTH, AIM, SHOTS, DEC_HEALTH, VEL_X, VEL_Y, VEL_Z, HEAD_X, HEAD_Y, HEAD_Z, AMMO, \
	PERFORMATIVE_OBJECTIVE, PERFORMATIVE_TARGET_REACHED, PERFORMATIVE_INIT, PERFORMATIVE_GAME, PERFORMATIVE_SHOOT, PERFORMATIVE_DATA, \
	PERFORMATIVE_GET, PERFORMATIVE_CFM, PERFORMATIVE_CFA, PERFORMATIVE_CFB, FOV, ENEMIES_IN_FOV, PACKS_IN_FOV, FRIENDS_IN_FOV, PACKS, PERFORMATIVE_PACK_TAKEN, PERFORMATIVE_FLAG_TAKEN, PERFORMATIVE_BDI, PERFORMATIVE_MOVE
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
MV_ALREADY_IN_DEST = 2


class BDITroop(AbstractAgent, BDIAgent):

	def __init__(self, jid, passwd, asl=None, team=TEAM_NONE, manager_jid="cmanager@localhost", service_jid="cservice@localhost"):

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

		# Destination Queue
		self.destinations = deque()

		super().__init__(jid, passwd,team=team, service_jid=service_jid)

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

		# Behaviour to handle Shot messages
		t = Template()
		t.set_metadata(PERFORMATIVE, PERFORMATIVE_SHOOT)
		self.add_behaviour(self.ShootResponderBehaviour(period=0), t)

		# Behaviour to inform manager our position, status, and so on
		t = Template()
		t.set_metadata(PERFORMATIVE, PERFORMATIVE_DATA)
		self.add_behaviour(self.DataFromTroopBehaviour(period=0.3), t)

		# Behaviour to increment inner variables (Power, Stamina and Health Bars)
		# self.agent.Launch_BarsAddOn_InnerBehaviour()
		self.add_behaviour(self.RestoreBehaviour(period=1))

		# Behaviour to call for medics or fieldops
		# t = Template()
		# t.set_metadata(PERFORMATIVE, PERFORMATIVE_GET)
		# self.add_behaviour(self.MedicAmmoRequestBehaviour(period=1), t)

		t = Template()
		t.set_metadata(PERFORMATIVE, PERFORMATIVE_BDI)
		self.add_behaviour(self.BDIBehaviour(), t)

		@self.bdi_actions.add(".goto", 3)
		def _goto(agent, term, intention):
			"""Sets the PyGomas destination. Expects args to be x,y,z"""
			self.destinations = deque()
			args = pyson.grounded(term.args, intention.scope)
			self.movement.destination.x = args[0]
			self.movement.destination.y = args[1]
			self.movement.destination.z = args[2]
			self.destinations.append(self.movement.destination)
			self.movement.calculate_new_orientation()
			self.bdi.set_belief(DESTINATION,args[0],args[1],args[2])
			self.bdi.set_belief(VELOCITY, self.movement.velocity.x,self.movement.velocity.y,self.movement.velocity.z)
			self.bdi.set_belief(HEADING, self.movement.heading.x,self.movement.heading.y,self.movement.heading.z)
			yield

		@self.bdi_actions.add(".create_control_points", 5)
		def _create_control_points(agent, term, intention):
			"""
			Calculates an array of positions for patrolling.
			When this action is called, it creates an array of n random positions.
			Expects args to be x,y,z,radius and number of points

			It's very useful to overload this action.
			"""
			args = pyson.grounded(term.args, intention.scope)

			center_x = args[0]
			center_y = args[1]
			center_z = args[2]
			radius = args[3]
			n = int(args[4])

			self.control_points = []  # Vector3D [iMaxCP]
			for i in range(n):
				while True:
					x = center_x + ((radius / 2) - (random.random() * radius))
					x = max(0, x)
					x = int(min(self.map.size_x - 1, x))
					y = 0
					z = center_z + ((radius / 2) - (random.random() * radius))
					z = max(0, z)
					z = int(min(self.map.size_z - 1, z))

					if self.check_static_position(x, z):
						if len(self.control_points):
							if (x,y,z) != self.control_points[i-1]:
								self.control_points.append((x, y, z))
								break
						else:
							self.control_points.append((x, y, z))
							break
				logger.success("Control point generated {}".format((x, y, z)))
			self.bdi.set_belief(CONTROL_POINTS, tuple(self.control_points))
			yield

		@self.bdi_actions.add(".shoot", 4)
		def _shoot(agent, term, intention):
			"""
			 The agent shoots in the direction at which he is aiming.

			 This method sends a FIPA INFORM message to Manager.
			 Once message is sent, the variable ammo is decremented.

			 :param shot_num: number of shots
			 :param X,Y,Z: position at which to shoot
			 :type shot_num: int
			 :type X,Y,Z: float
			 :returns True (shot done) | False (cannot shoot, has no ammo)
			 :rtype bool
			 """
			args = pyson.grounded(term.args, intention.scope)

			shot_num = args[0]
			victim_x = args[1]
			victim_y = args[2]
			victim_z = args[3]

			class ShootBehaviour(OneShotBehaviour):
				async def run(self):
					if self.agent.ammo <= MIN_AMMO:
						return False

					# Fill the REQUEST message
					msg = Message()
					msg.to = self.agent.manager
					msg.set_metadata(PERFORMATIVE, PERFORMATIVE_SHOOT)
					content = {NAME: self.agent.name, AIM: self.agent.threshold.get_aim(),
							   SHOTS: min(self.agent.threshold.get_shot(),shot_num),
							   X:victim_x,Y:victim_y,Z:victim_z}
					logger.info("{} shot!".format(content[NAME]))
					msg.body = json.dumps(content)
					await self.send(msg)

					self.agent.ammo -= 1
					return True

			b = ShootBehaviour()
			self.add_behaviour(b)
			yield

		@self.bdi_actions.add(".get_medics", 0)
		def _get_medics(agent, term, intention):
			"""Request for medic agents. This action sends a FIPA REQUEST
			   message to the service agent asking for those who offer the 
			   Medic service.
			   """
			class GetMedicBehaviour(OneShotBehaviour):
				async def run(self):
					msg = Message()
					msg.set_metadata(PERFORMATIVE, PERFORMATIVE_GET)
					msg.to = self.agent.service_jid
					msg.body = json.dumps({NAME: MEDIC_SERVICE, TEAM: self.agent.team})
					await self.send(msg)
					result = await self.receive(timeout=LONG_RECEIVE_WAIT)
					if result:
						result = json.loads(result.body)
						self.agent.medics_count = len(result)
						logger.info("{} got {} medics: {}".format(
							self.agent.name, self.agent.medics_count, result))
						self.agent.bdi.set_belief(MY_MEDICS,tuple(result))
					else:
						self.agent.bdi.set_belief(MY_MEDICS,tuple("None"))
						self.agent.medics_count = 0

			b = GetMedicBehaviour()
			self.add_behaviour(b)
			yield

		@self.bdi_actions.add(".stop", 0)
		def _stop(agent, term, intention):
			"""Stops the PyGomas agent. """
			self.movement.destination.x = self.movement.position.x
			self.movement.destination.y = self.movement.position.y
			self.movement.destination.z = self.movement.position.z
			yield

		future = super().start(auto_register)
		return future

	class CreateBasicTroopBehaviour(OneShotBehaviour):
		async def run(self):
			if self.agent.service_types is not None:
				for service in self.agent.service_types:
					self.agent.register_service(str(service))

			msg = Message(to=self.agent.manager)
			msg.set_metadata(PERFORMATIVE, PERFORMATIVE_INIT)
			msg.body = json.dumps({NAME: self.agent.name, TYPE: str(
				self.agent.eclass), TEAM: str(self.agent.team)})
			await self.send(msg)

	class MoveBehaviour(PeriodicBehaviour):
		async def on_start(self):
			self.agent.last_time_move_attempt = time.time()

		async def run(self):
			current_time = time.time()
			dt = current_time - self.agent.last_time_move_attempt
			self.agent.last_time_move_attempt = current_time

			absx = abs(self.agent.movement.destination.x -
					   self.agent.movement.position.x)
			absz = abs(self.agent.movement.destination.z -
					   self.agent.movement.position.z)
			if (absx < PRECISION_X) and (absz < PRECISION_Z):
				if self.agent.movement.position != self.agent.movement.destination:
					print("\n\nARRIVED\n\n")
					self.agent.movement.position = Vector3D(
						self.agent.movement.destination)
					self.agent.bdi.set_belief(
							PERFORMATIVE_TARGET_REACHED,self.agent.movement.destination.x,self.agent.movement.destination.y,self.agent.movement.destination.z)
					for i in range(2):
						if self.agent.destinations:
							self.agent.movement.destination = self.agent.destinations.popleft()

					last_velocity = Vector3D(self.agent.movement.velocity)
					last_heading = Vector3D(self.agent.movement.heading)
					self.agent.movement.calculate_new_orientation()

					if last_velocity != self.agent.movement.velocity:
						self.agent.bdi.set_belief(VELOCITY,self.agent.movement.velocity.x,self.agent.movement.velocity.y,self.agent.movement.velocity.z)
					if last_heading != self.agent.movement.heading:
						self.agent.bdi.set_belief(HEADING,self.agent.movement.heading.x,self.agent.movement.heading.y,self.agent.movement.heading.z)
			else:
				move_result = self.agent.move(dt)
				if move_result == MV_OK:
					self.agent.bdi.set_belief(POSITION,self.agent.movement.position.x,self.agent.movement.position.y,self.agent.movement.position.z)
				elif move_result == MV_CANNOT_GET_POSITION:
					self.agent.generate_intermediate_point()
				elif move_result == MV_ALREADY_IN_DEST:
					pass

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
				self.agent.movement.set_size(
					self.agent.map.get_size_x(), self.agent.map.get_size_z())

				self.agent.generate_spawn_position()
				self.agent.setup_priorities()

				t = Template()
				t.set_metadata(PERFORMATIVE, PERFORMATIVE_MOVE)
				self.agent.add_behaviour(self.agent.MoveBehaviour(
					period=INTERVAL_TO_MOVE), t)

				self.kill()

	# Behaviour to get the objective of the game, to create the corresponding task
	class ObjectiveBehaviour(CyclicBehaviour):
		async def run(self):
			logger.info("{} waiting for objective.".format(self.agent.name))
			msg = await self.receive(timeout=LONG_RECEIVE_WAIT)
			if msg:
				content = json.loads(msg.body)
				if self.agent.bdi_enabled:
					if self.agent.team == TEAM_ALLIED:
						x = ((self.agent.map.allied_base.get_end_x() -
							  self.agent.map.allied_base.get_init_x()) / 2) + \
							self.agent.map.allied_base.get_init_x()
						y = ((self.agent.map.allied_base.get_end_y() -
							  self.agent.map.allied_base.get_init_y()) / 2) + \
							self.agent.map.allied_base.get_init_y()
						z = ((self.agent.map.allied_base.get_end_z() -
							  self.agent.map.allied_base.get_init_z()) / 2) + \
							self.agent.map.allied_base.get_init_z()
					elif self.agent.team == TEAM_AXIS:
						x = ((self.agent.map.axis_base.get_end_x() -
							  self.agent.map.axis_base.get_init_x()) / 2) + \
							self.agent.map.axis_base.get_init_x()
						y = ((self.agent.map.axis_base.get_end_y() -
							  self.agent.map.axis_base.get_init_y()) / 2) + \
							self.agent.map.axis_base.get_init_y()
						z = ((self.agent.map.axis_base.get_end_z() -
							  self.agent.map.axis_base.get_init_z()) / 2) + \
							self.agent.map.axis_base.get_init_z()
					self.agent.bdi.set_belief(TEAM,self.agent.team)
					self.agent.bdi.set_belief(BASE,x,y,z)
					self.agent.bdi.set_belief(POSITION,self.agent.movement.position.x,self.agent.movement.position.y,self.agent.movement.position.z)
					self.agent.bdi.set_belief(HEALTH,self.agent.health)
					self.agent.bdi.set_belief(THRESHOLD_HEALTH,self.agent.threshold.health)
					self.agent.bdi.set_belief(THRESHOLD_AMMO,self.agent.threshold.ammo)
					self.agent.bdi.set_belief(THRESHOLD_AIM,self.agent.threshold.aim)
					self.agent.bdi.set_belief(THRESHOLD_SHOTS,self.agent.threshold.shot)
					self.agent.bdi.set_belief(FLAG, content[X], content[Y], content[Z])
				logger.info("Team: {}, agent: {}, has its objective at {}".format(
					self.agent.team,self.agent.name, content))
				self.kill()

	# Behaviour to listen to manager if game has finished
	class GameFinishedBehaviour(CyclicBehaviour):
		async def run(self):
			msg = await self.receive(timeout=LONG_RECEIVE_WAIT)
			if msg:
				logger.info("[" + self.agent.name + "]: Bye!")
				self.kill()
				await self.agent.die()
		
	# Behaviour to handle Shot messages
	class ShootResponderBehaviour(PeriodicBehaviour):
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
			try:
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
					print("Stepped on pack")
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
						if s.team == TEAM_NONE:
							self.agent.bdi.set_belief(PACKS_IN_FOV,idx,int(obj[TYPE]),float(obj[ANGLE]),float(obj[DISTANCE]),int(obj[HEALTH]),float(obj[X]),float(obj[X]),float(obj[Z]))
						elif s.team == self.agent.team:
							self.agent.bdi.set_belief(FRIENDS_IN_FOV,idx,int(obj[TYPE]),float(obj[ANGLE]),float(obj[DISTANCE]),int(obj[HEALTH]),float(obj[X]),float(obj[X]),float(obj[Z]))
						else:
							self.agent.bdi.set_belief(ENEMIES_IN_FOV,idx,int(obj[TYPE]),float(obj[ANGLE]),float(obj[DISTANCE]),int(obj[HEALTH]),float(obj[X]),float(obj[X]),float(obj[Z]))

			except ZeroDivisionError:
				pass

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


	# Behaviour to launch the FSM
	def launch_fsm_behaviour(self):

		# FSM Declaration
		self.fsm_behaviour = FSMBehaviour()

		# Register state STATE_STANDING (first state)
		self.fsm_behaviour.add_state(
			STATE_STANDING, self.StandingState(), initial=True)

		# Register state STATE_GOTO_TARGET
		self.fsm_behaviour.add_state(STATE_GOTO_TARGET, self.GoToTargetState())

		# Register state STATE_TARGET_REACHED
		self.fsm_behaviour.add_state(
			STATE_TARGET_REACHED, self.TargetReachedState())

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
		self.fsm_behaviour.add_transition(
			STATE_GOTO_TARGET, STATE_TARGET_REACHED)
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

		logger.info(
			"Spawn position for agent {} is ({}, {})".format(self.name, x, z))

		self.movement.position.x = x
		self.movement.position.y = 0
		self.movement.position.z = z

	def move(self, dt):
		new_position = Vector3D(self.movement.calculate_position(dt))
		if not self.check_static_position(new_position.x, new_position.z):
			logger.info(self.name + ": Can't walk to {}. I stay at {}".format(new_position, self.movement.position
																			  ))
			return MV_CANNOT_GET_POSITION
		elif new_position == self.movement.position:
			return MV_ALREADY_IN_DEST
		else:
			self.movement.position = Vector3D(new_position)
			return MV_OK

	# Behaviours to handle our FSM
	class StandingState(State):
		async def run(self):
			num_tasks = len(self.agent.task_manager)
			if num_tasks <= 0:
				self.set_next_state(STATE_STANDING)
				logger.info(self.agent.name +
							": Behaviour ............ NO TASKS!!!")
				await asyncio.sleep(1.0)
				return

			if self.agent.health <= 0:
				self.agent.task_manager.clear()
				# if we have nothing to do, go to QUIT state
				self.set_next_state(STATE_QUIT)

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

	class TargetReachedState(State):

		async def run(self):
			logger.success(self.agent.name +
						   ": Behaviour ............ [TARGET REACHED]")
			logger.trace("position: {} destination: {}"
						 .format(self.agent.movement.position, self.agent.movement.destination))

			task = self.agent.task_manager.get_current_task()

			# if self.agent.task_manager.get_current_task().is_erasable:
			logger.info("Deleting task: {}".format(task))
			self.agent.task_manager.delete(task)

			self.agent.perform_target_reached(task)

			self.set_next_state(STATE_STANDING)

			return

	class FightingState(State):

		async def run(self):
			logger.info(self.agent.name +
						": Behaviour ............ [FIGHTING]")
			self.set_next_state(STATE_FIGHTING)
			await asyncio.sleep(0.5)
			return

	# Non-overloadable Methods, interesting for user

	def pack_taken(self, pack_type, quantity):
		print("GOT PACK")
		if pack_type == PACK_MEDICPACK:
			print("Increasing health")
			self.bdi.set_belief(PERFORMATIVE_PACK_TAKEN,MEDIC_SERVICE,quantity)
			self.increase_health(quantity)
		elif pack_type == PACK_AMMOPACK:
			self.bdi.set_belief(PERFORMATIVE_PACK_TAKEN,AMMO_SERVICE,quantity)
			self.increase_ammo(quantity)
		elif pack_type == PACK_OBJPACK:
			self.objective_pack_taken()
			self.bdi.set_belief(PERFORMATIVE_FLAG_TAKEN)

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
		self.bdi.set_belief(HEALTH, self.health)

	def decrease_health(self, quantity):
		"""
		Decrements the current health of the agent.

		:param quantity: negative quantity to decrement
		"""
		self.health -= quantity
		if self.health < MIN_HEALTH:
			self.health = MIN_HEALTH
		self.bdi.set_belief(HEALTH, self.health)

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
		self.bdi.set_belief(AMMO, self.ammo)

	def decrease_ammo(self, quantity):
		"""
		Decrements the current ammunition of the agent.

		:param quantity: negative quantity to decrement
		"""
		self.ammo -= quantity
		if self.ammo < MIN_AMMO:
			self.ammo = MIN_AMMO
		self.bdi.set_belief(AMMO, self.ammo)

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

			logger.info("{} got {} medics: {}".format(
				self.name, self.medics_count, result))

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
			self.task_manager.add_task(
				TASK_PATROLLING, self.name, new_position)

		elif current_task.type == TASK_WALKING_PATH:
			self.a_star_path_index += 1
			if self.a_star_path_index >= len(self.a_star_path):
				self.a_star_path_index = 0
				current_task.is_erasable = True
			else:
				new_position = {X: self.a_star_path[self.a_star_path_index].x,
								Y: self.a_star_path[self.a_star_path_index].y,
								Z: self.a_star_path[self.a_star_path_index].z}
				self.task_manager.add_task(
					TASK_WALKING_PATH, self.name, new_position)

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
			self.movement.calculate_new_destination(
				radius_x=ESCAPE_RADIUS, radius_y=ESCAPE_RADIUS)
			if self.check_static_position(self.movement.destination.x, self.movement.destination.z):
				self.movement.calculate_new_orientation()
				return

	def generate_intermediate_point(self):
		"""
		Calculates an intermediate point to go to between actual position and destination.

		This method is called when the agent generates a position which is not valid in the map.
		"""
		logger.info(
			f"{self.name} Current Position: {self.movement.position.x}, {self.movement.position.z}")
		new_destination = Vector3D(self.movement.calculate_new_destination(
			radius_x=DEFAULT_RADIUS, radius_y=DEFAULT_RADIUS))
		logger.info(
			f"{self.name} New Position: {new_destination.x}, {new_destination.z}")
		if self.check_static_position(new_destination.x, new_destination.z):
			self.destinations.appendleft(new_destination)
			self.movement.destination = new_destination
			return True
		else:
			return False

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
