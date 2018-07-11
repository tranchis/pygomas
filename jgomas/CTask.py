from jgomas.Vector3D import Vector3D


class CTask:

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

    m_Index = 0

    task_name = {TASK_NONE: 'NONE',
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

    def __init__(self):
        self.m_jid = ""
        self.m_iType = 0
        self.m_iPriority = 0
        self.m_StampTime = 0
        self.m_iData = 0
        self.m_fData = 0.0
        self.m_iPacksDelivered = 0
        self.m_ObjPointer = None
        self.m_Position = Vector3D()
        self.m_bErasable = True
        CTask.m_Index = CTask.m_Index + 1
        self.m_id = CTask.m_Index

    def __repr__(self):
        return "T("+str(self.m_id)+","+str(self.jid.split('@')[0])+")=["+str(self.m_iPriority)+","+str(self.task_name[self.m_iType])+","+str(self.m_Position)+"]"

    def getPacksDelivered(self):
        return self.m_iPacksDelivered

    def getType(self):
        return self.m_iType

    def getPriority(self):
        return self.m_iPriority

    def getPosition(self):
        return self.m_Position

    def setPriority(self, _iPriority):
        self.m_iPriority = _iPriority

    """
    def setPosition(self, _Position):
        self.m_Position.x = _Position.x
        self.m_Position.y = _Position.y
        self.m_Position.z = _Position.z
    """
