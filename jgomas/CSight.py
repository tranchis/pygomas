from jgomas.Vector3D import Vector3D


class CSight:

    def __init__(self):
        self.m_Position = Vector3D()
        self.m_id = 0
        self.m_eTeam = 0
        self.m_eType = 0
        self.m_dDistance = 0.0
        self.m_dAngle = 0.0
        self.m_iHealth = 0

    def getAngle(self):
        return self.m_dAngle

    def getDistance(self):
        return self.m_dDistance

    def getTeam(self):
        return self.m_eTeam

    def getType(self):
        return self.m_eType

    def getHealth(self):
        return self.m_iHealth

    def getPosition(self):
        return self.m_Position
