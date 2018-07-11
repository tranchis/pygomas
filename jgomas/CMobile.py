import random
import math
from jgomas.Vector3D import Vector3D


class CMobile:

    m_Random = random

    def __init__(self):
        self.m_Position = Vector3D()
        self.m_Destination = Vector3D()
        self.m_Velocity = Vector3D()
        self.m_Heading = Vector3D()
        self.m_dViewRadius = 50.0
        self.m_dAngle = 1.0
        self.m_MinX = self.m_MinZ = self.m_MaxX = self.m_MaxZ = 0

    def SetSize(self, _MaxX, _MaxZ):
        self.m_MinX = 8
        self.m_MinZ = 8
        self.m_MaxX = (_MaxX * 8) - 8
        self.m_MaxZ = (_MaxZ * 8) - 8

    def CalculatePosition(self, _dt):

        t = _dt

        self.m_Position.x += (self.m_Velocity.x * t)
        self.m_Position.y += 0.0  # (m_Velocity.y * t) + (0.5f * t2);
        self.m_Position.z += (self.m_Velocity.z * t)

        return True

    def CalculateNewOrientation(self):
        dx = float(self.m_Destination.x - self.m_Position.x)
        dy = float(self.m_Destination.y - self.m_Position.y)
        dz = float(self.m_Destination.z - self.m_Position.z)
        f2Norma = math.sqrt((dx*dx + dy*dy + dz*dz))

        if f2Norma > 0:
            self.m_Velocity.x = float(dx / f2Norma)
            self.m_Velocity.y = float(dy / f2Norma)
            self.m_Velocity.z = float(dz / f2Norma)

        if self.m_Velocity.length() > 0.0001:
            self.m_Heading.x = self.m_Velocity.x
            self.m_Heading.y = self.m_Velocity.y
            self.m_Heading.z = self.m_Velocity.z

        self.m_Velocity.x *= 2
        self.m_Velocity.y *= 2
        self.m_Velocity.z *= 2

    def CalculateNewDestination(self, _iRadiusX, _iRadiusY):
        x = self.m_Position.x + \
            ((random.random() * (_iRadiusX * 2)) - _iRadiusX)
        z = self.m_Position.z + \
            ((random.random() * (_iRadiusY * 2)) - _iRadiusY)

        if x < self.m_MinX:
            x = self.m_MinX
        if x >= self.m_MaxX:
            x = self.m_MaxX
        if z < self.m_MinZ:
            z = self.m_MinZ
        if z > self.m_MaxZ:
            z = self.m_MaxZ

        self.m_Destination.x = x
        self.m_Destination.y = 0.0
        self.m_Destination.z = z
        # print "NUEVO DESTINO CALCULADO: (" + str(x) + ", " + str(z) + ")"

    def getDestination(self):
        return self.m_Destination

    def setDestination(self, destination):
        self.m_Destination = destination

    def getPosition(self):
        return self.m_Position

    def getdAngle(self):
        return self.m_dAngle

    def getdViewRadius(self):
        return self.m_dViewRadius

    def getHeading(self):
        return self.m_Heading

    def getVelocity(self):
        return self.m_Velocity
