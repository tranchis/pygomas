import random
import math
from .vector import Vector3D


class Mobile(object):

    def __init__(self):
        self.position = Vector3D()
        self.destination = Vector3D()
        self.velocity = Vector3D()
        self.heading = Vector3D()
        self.view_radius = 50.0
        self.angle = 1.0
        self.min_x = self.min_z = self.max_x = self.max_z = 0

    def set_size(self, max_x, max_z):
        self.min_x = 8
        self.min_z = 8
        self.max_x = (max_x * 8) - 8
        self.max_z = (max_z * 8) - 8

    def calculate_position(self, dt):

        self.position.x += (self.velocity.x * dt)
        self.position.y += 0.0  # (m_Velocity.y * t) + (0.5f * t2);
        self.position.z += (self.velocity.z * dt)

        return True

    def calculate_new_orientation(self):
        dx = float(self.destination.x - self.position.x)
        dy = float(self.destination.y - self.position.y)
        dz = float(self.destination.z - self.position.z)
        f2_norma = math.sqrt((dx * dx + dy * dy + dz * dz))

        if f2_norma > 0:
            self.velocity.x = float(dx / f2_norma)
            self.velocity.y = float(dy / f2_norma)
            self.velocity.z = float(dz / f2_norma)

        if self.velocity.length() > 0.0001:
            self.heading.x = self.velocity.x
            self.heading.y = self.velocity.y
            self.heading.z = self.velocity.z

        self.velocity.x *= 2
        self.velocity.y *= 2
        self.velocity.z *= 2

    def calculate_new_destination(self, radius_x, radius_y):
        x = self.position.x + ((random.random() * (radius_x * 2)) - radius_x)
        z = self.position.z + ((random.random() * (radius_y * 2)) - radius_y)

        if x < self.min_x:
            x = self.min_x
        if x >= self.max_x:
            x = self.max_x
        if z < self.min_z:
            z = self.min_z
        if z > self.max_z:
            z = self.max_z

        self.destination.x = x
        self.destination.y = 0.0
        self.destination.z = z
        # print "NUEVO DESTINO CALCULADO: (" + str(x) + ", " + str(z) + ")"

    def get_destination(self):
        return self.destination

    def set_destination(self, destination):
        self.destination = destination

    def get_position(self):
        return self.position

    def get_angle(self):
        return self.angle

    def get_view_radius(self):
        return self.view_radius

    def get_heading(self):
        return self.heading

    def get_velocity(self):
        return self.velocity
