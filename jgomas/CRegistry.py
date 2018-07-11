import random
from jgomas.CService import CService


class CRegistry:

    MAX_TOTAL_SERVICES = 100

    def __init__(self):
        self.m_ServiceTypes = list()
        self.m_ServiceList = list()

    def RegisterService(self, _sServiceType, _bKeyCode=True):

        for i in self.m_ServiceList:
            if _sServiceType in i.m_sDFType:
                print("Service registered earlier: " + _sServiceType)
                return i

        # If we are here, we haven't found any match
        Service = CService()

        sKeyName = ""
        sKeyType = ""

        if _bKeyCode:
            sKeyName = str(random.randint(0, 9999))
            sKeyType = str(random.randint(0, 9999))

        Service.m_sDFName = _sServiceType + sKeyName
        Service.m_sDFType = _sServiceType + sKeyType

        self.m_ServiceList.append(Service)
        self.m_ServiceTypes.append(_sServiceType)
        print("Registry - Service Registered: " + _sServiceType)

        return Service
