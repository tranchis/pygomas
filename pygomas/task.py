import time
from pqdict import maxpq
from loguru import logger

from .ontology import X, Y, Z
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
TASK_RETURN_TO_BASE = 11
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
             TASK_STOP_WALKING: 'STOP_WALKING',
             TASK_RETURN_TO_BASE: 'RETURN_TO_BASE'
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


class TaskManager(object):

    def __init__(self):
        self.tasks = dict()
        self.tasks_heap = maxpq()
        self.current_task = None
        self.task_priority = dict()

    def add_task(self, task_type, jid, content, priority=None):
        """
        Adds a task to the task list with a modified priority.

        This method adds a task to the task list with the priority passed as parameter, non the standard priority.
        If there is a task of same type and same owner, it doesn't create a new task:
        simply substitutes some attributes with newer values.

        :param task_type: one of the defined types of tasks.
        :param jid: the agent that induces the creation of the task.
        :param content: is a position: ( x , y , z ).
        :param priority: priority of task
        """

        logger.info("Adding task type: {} owner: {}, content: {}".format(task_type, jid, content))
        if priority is None:
            priority = self.task_priority[task_type]

        if task_type in self.tasks.keys():
            task = self.tasks[(task_type, jid)]

        else:
            task = Task()
            task.jid = jid
            task.type = task_type
            #if task_type in [TASK_PATROLLING, TASK_WALKING_PATH, TASK_GET_OBJECTIVE]:
            #    task.is_erasable = False

        task.priority = priority
        task.stamp_time = time.time()

        task.position.x = float(content[X])
        task.position.y = float(content[Y])
        task.position.z = float(content[Z])

        self.tasks[(task_type, jid)] = task
        try:
            self.tasks_heap.additem(task, priority)
        except KeyError:
            self.tasks_heap.pop(task)
            self.tasks_heap.additem(task, priority)

    def get_current_task(self):
        return self.current_task

    def set_priority(self, task_type, priority):
        self.task_priority[task_type] = priority

    def clear(self):
        self.tasks = dict()
        self.tasks_heap.clear()

    def select_highest_priority_task(self):
        task = self.tasks_heap.top()
        self.current_task = task

    def delete(self, task):
        task_type, jid = task.type, task.jid
        self.tasks_heap.pop(self.tasks[(task_type, jid)])
        del self.tasks[(task_type, jid)]

    def __len__(self):
        return len(self.tasks)
