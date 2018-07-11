from jgomas.Vector3D import Vector3D
from jgomas.CConfig import CConfig


class CBase:

    def __init__(self):
        self.m_Init = Vector3D()
        self.m_End = Vector3D()

    def GetInitX(self):
        return self.m_Init.x

    def GetInitY(self):
        return self.m_Init.y

    def GetInitZ(self):
        return self.m_Init.z

    def GetEndX(self):
        return self.m_End.x

    def GetEndY(self):
        return self.m_End.y

    def GetEndZ(self):
        return self.m_End.z


class CTerrain:
    def __init__(self):
        self.m_dHeight = 0.0
        self.m_bCanWalk = False
        self.m_iCost = 0

    def __str__(self):
        if self.m_bCanWalk:
            return "_"
        else:
            return "*"

    def __repr__(self):
        return self.__str__()


class CTerrainMap:

    def __init__(self):

        self.m_Terrain = None
        self.m_AlliedBase = CBase()
        self.m_AxisBase = CBase()
        self.m_Target = Vector3D()

        self.m_iSizeX = 0
        self.m_iSizeZ = 0

    def GetSizeX(self):
        return self.m_iSizeX

    def GetSizeZ(self):
        return self.m_iSizeZ

    def GetTargetX(self):
        return self.m_Target.x

    def GetTargetY(self):
        return self.m_Target.y

    def GetTargetZ(self):
        return self.m_Target.z

    def CanWalk(self, x, z):
        if x < 0 or z < 0 or x >= self.m_iSizeX \
                or z >= self.m_iSizeZ or not self.m_Terrain:
            return False

        return self.m_Terrain[x][z].m_bCanWalk

    def GetCost(self, x, z):
        if x < 0 or z < 0 or x >= self.m_iSizeX \
                or z >= self.m_iSizeZ or not self.m_Terrain:
            return 2 * 10000

        return self.m_Terrain[x][z].m_iCost

    def LoadMap(self, _sMainFile, config):

        sLine = ""
        sCostMapName = ""

        file = open(config.m_dataPath + _sMainFile + "/" + _sMainFile + ".txt")

        sLine = file.readline()  # [JADE]
        sLine = file.readline()  # JADE_OBJECTIVE:  x y
        tokens = sLine.split()
        # JADE_OBJECTIVE:
        self.m_Target.x = int(tokens[1]) * 8  # x
        self.m_Target.y = 0
        self.m_Target.z = int(tokens[2]) * 8  # y
        print(" OBJECTIVE: (", str(self.m_Target.x), ",",
              str(self.m_Target.z), ")")

        sLine = file.readline()  # JADE_SPAWN_ALLIED: x1 y1 x2 y2
        tokens = sLine.split()
        # JADE_OBJECTIVE:
        self.m_AlliedBase.m_Init.x = int(tokens[1]) * 8  # x1
        self.m_AlliedBase.m_Init.z = int(tokens[2]) * 8  # z1
        self.m_AlliedBase.m_End.x = int(tokens[3]) * 8  # x2
        self.m_AlliedBase.m_End.z = int(tokens[4]) * 8  # z2
        print(" ALLIED BASE: (", self.m_AlliedBase.m_Init.x, ",",
              self.m_AlliedBase.m_Init.z, ") (", self.m_AlliedBase.m_End.x,
              ",", self.m_AlliedBase.m_End.z, ")")

        sLine = file.readline()  # JADE_SPAWN_AXIS: x1 y1 x2 y2
        tokens = sLine.split()
        # JADE_OBJECTIVE:
        self.m_AxisBase.m_Init.x = int(tokens[1]) * 8  # x1
        self.m_AxisBase.m_Init.z = int(tokens[2]) * 8  # z1
        self.m_AxisBase.m_End.x = int(tokens[3]) * 8  # x2
        self.m_AxisBase.m_End.z = int(tokens[4]) * 8  # z2
        print(" AXIS BASE: (", self.m_AxisBase.m_Init.x, ",",
              self.m_AxisBase.m_Init.z, ") (", self.m_AxisBase.m_End.x, ",",
              self.m_AxisBase.m_End.z, ")")

        sLine = file.readline()  # JADE_COST_MAP: w h name
        tokens = sLine.split()
        # JADE_COST_MAP:
        self.m_iSizeX = int(tokens[1])
        self.m_iSizeZ = int(tokens[2])
        sCostMapName = tokens[3]
        print(" COST MAP: (", self.m_iSizeX, " x ", self.m_iSizeZ, ") ",
              sCostMapName)

        file.close()

        if self.m_iSizeX <= 0 or self.m_iSizeZ <= 0:
            print("Invalid Cost Map")
            return

        self.m_Terrain = []
        for i in range(self.m_iSizeX):
            self.m_Terrain.append([])
            for j in range(self.m_iSizeZ):
                self.m_Terrain[i].append(CTerrain())

        file = open(config.m_dataPath + _sMainFile + "/" + sCostMapName)

        for z in range(self.m_iSizeZ):
            for x in range(self.m_iSizeX):
                c = file.read(1)
                while c == '\n' or c == "\r":
                    c = file.read(1)  # read next char
                if c == '*':
                    self.m_Terrain[x][z].m_bCanWalk = False
                    self.m_Terrain[x][z].m_iCost = 10000
                elif c == ' ':
                    self.m_Terrain[x][z].m_bCanWalk = True
                    self.m_Terrain[x][z].m_iCost = 1
                self.m_Terrain[x][z].m_dHeight = 0.0
        file.close()

    def __str__(self):
        s = ""

        for z in range(self.m_iSizeZ):
            for x in range(self.m_iSizeX):
                s += str(self.m_Terrain[x][z])
            s += "\n"
        return s
