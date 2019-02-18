from .vector import Vector3D

TASK_NONE = 0
TASK_GIVE_MEDICPAKS = 1
TASK_GIVE_AMMOPACKS = 2
TASK_GIVE_BACKUP = 3
TASK_GET_OBJECTIVE = 4
TASK_ATTACK = 5
TASK_RUN_AWAY = 6
TASK_GOTO_POSITION = 7
TASK_PATROLLING = 8
TASK_WALKING_PATH = 9
TASK_STOP_WALKING = 10
MAX_TASK = 100

TASK_NAME = {TASK_NONE: 'NONE',
             TASK_GIVE_MEDICPAKS: 'GIVE_MEDICPACKS',
             TASK_GIVE_AMMOPACKS: 'GIVE_AMMOPACKS',
             TASK_GIVE_BACKUP: 'GIVE_BACKUP',
             TASK_GET_OBJECTIVE: 'GET_OBJECTIVE',
             TASK_ATTACK: 'ATTACK',
             TASK_RUN_AWAY: 'RUN_AWAY',
             TASK_GOTO_POSITION: 'GOTO_POSITION',
             TASK_PATROLLING: 'PATROLLING',
             TASK_WALKING_PATH: 'WALKING_PATH',
             TASK_STOP_WALKING: 'STOP_WALKING'
             }


class Task(object):
    index = 0

    def __init__(self):
        self.jid = ""
        self.type = 0
        self.priority = 0
        self.stamp_time = 0
        self.data = 0
        self.float_data = 0.0
        self.packs_delivered = 0
        self.obj_pointer = None
        self.position = Vector3D()
        self.is_erasable = True
        Task.index = Task.index + 1
        self.task_id = Task.index

    def __repr__(self):
        return "T(" + str(self.task_id) + "," + str(self.jid.split('@')[0]) + ")=[" + str(self.priority) + "," + \
               str(TASK_NAME[self.type]) + "," + str(self.position) + "]"

    def get_packs_delivered(self):
        return self.packs_delivered

    def get_type(self):
        return self.type

    def get_priority(self):
        return self.priority

    def get_position(self):
        return self.position

    def set_priority(self, priority: int):
        self.priority = priority

    """
    def set_position(self, _Position):
        self.m_Position.x = _Position.x
        self.m_Position.y = _Position.y
        self.m_Position.z = _Position.z
    """
