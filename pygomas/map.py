import os

from loguru import logger

from .vector import Vector3D


class Base:
    def __init__(self):
        self.init = Vector3D()
        self.end = Vector3D()

    def get_init_x(self):
        return self.init.x

    def get_init_y(self):
        return self.init.y

    def get_init_z(self):
        return self.init.z

    def get_end_x(self):
        return self.end.x

    def get_end_y(self):
        return self.end.y

    def get_end_z(self):
        return self.end.z


class Terrain:
    def __init__(self):
        self.height = 0.0
        self.can_walk = False
        self.cost = 0

    def __str__(self):
        if self.can_walk:
            return "_"
        else:
            return "*"

    def __repr__(self):
        return self.__str__()


class TerrainMap:
    def __init__(self):
        self.terrain = None
        self.allied_base = Base()
        self.axis_base = Base()
        self.target = Vector3D()

        self.size_x = 0
        self.size_z = 0

    def get_size_x(self):
        return self.size_x

    def get_size_z(self):
        return self.size_z

    def get_target_x(self):
        return self.target.x

    def get_target_y(self):
        return self.target.y

    def get_target_z(self):
        return self.target.z

    def can_walk(self, x, z):
        if x < 0 or z < 0 or x >= self.size_x or z >= self.size_z or not self.terrain:
            logger.info("Can't walk outside the map! {}:{} <> {}:{}".format(x, z, self.size_x, self.size_z))
            return False

        # logger.info("self.terrain[{}][{}]: {}".format(x, z, self.terrain[x][z]))
        return self.terrain[x][z].can_walk

    def get_cost(self, x, z):
        if x < 0 or z < 0 or x >= self.size_x or z >= self.size_z or not self.terrain:
            return 2 * 10000

        return self.terrain[x][z].cost

    def load_map(self, main_file, config):

        file = open(config.data_path + main_file + os.sep + main_file + ".txt")

        _ = file.readline()  # [JADE]
        line = file.readline()  # JADE_OBJECTIVE:  x y
        tokens = line.split()
        # JADE_OBJECTIVE:
        self.target.x = int(tokens[1]) * 8  # x
        self.target.y = 0
        self.target.z = int(tokens[2]) * 8  # y
        logger.info(f" OBJECTIVE: ( {self.target.x}, {self.target.z} )")

        line = file.readline()  # JADE_SPAWN_ALLIED: x1 y1 x2 y2
        tokens = line.split()
        # JADE_OBJECTIVE:
        self.allied_base.init.x = int(tokens[1]) * 8  # x1
        self.allied_base.init.z = int(tokens[2]) * 8  # z1
        self.allied_base.end.x = int(tokens[3]) * 8  # x2
        self.allied_base.end.z = int(tokens[4]) * 8  # z2
        logger.info(f" ALLIED BASE: ({self.allied_base.init.x}, {self.allied_base.init.z})"
                    f" ({self.allied_base.end.x}, {self.allied_base.end.z})")

        line = file.readline()  # JADE_SPAWN_AXIS: x1 y1 x2 y2
        tokens = line.split()
        # JADE_OBJECTIVE:
        self.axis_base.init.x = int(tokens[1]) * 8  # x1
        self.axis_base.init.z = int(tokens[2]) * 8  # z1
        self.axis_base.end.x = int(tokens[3]) * 8  # x2
        self.axis_base.end.z = int(tokens[4]) * 8  # z2
        logger.info(f" AXIS BASE: ({self.axis_base.init.x}, {self.axis_base.init.z}) "
                    f"({self.axis_base.end.x}, {self.axis_base.end.z}")

        line = file.readline()  # JADE_COST_MAP: w h name
        tokens = line.split()
        # JADE_COST_MAP:
        self.size_x = int(tokens[1])
        self.size_z = int(tokens[2])
        cost_map_name = tokens[3]
        logger.info(f" COST MAP: ({self.size_x} x {self.size_z}) {cost_map_name}")

        file.close()

        if self.size_x <= 0 or self.size_z <= 0:
            logger.info("Invalid Cost Map")
            return

        self.terrain = []
        for i in range(self.size_x):
            self.terrain.append([])
            for j in range(self.size_z):
                self.terrain[i].append(Terrain())

        file = open(config.data_path + main_file + os.sep + cost_map_name)

        for z in range(self.size_z):
            for x in range(self.size_x):
                c = file.read(1)
                while c == '\n' or c == "\r":
                    c = file.read(1)  # read next char
                if c == '*':
                    self.terrain[x][z].can_walk = False
                    self.terrain[x][z].cost = 10000
                elif c == ' ':
                    self.terrain[x][z].can_walk = True
                    self.terrain[x][z].cost = 1
                self.terrain[x][z].height = 0.0
        file.close()

    def __str__(self):
        s = ""

        for z in range(self.size_z):
            for x in range(self.size_x):
                s += str(self.terrain[x][z])
            s += "\n"
        return s
