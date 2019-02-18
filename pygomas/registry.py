import random
from loguru import logger

from .service import Service

MAX_TOTAL_SERVICES = 100


class Registry:

    def __init__(self):
        self.service_types = list()
        self.services = list()

    def register_service(self, service_type, is_key_code=True):

        for s in self.services:
            if service_type in s.df_type:
                logger.info("Service registered earlier: " + service_type)
                return s

        # If we are here, we haven't found any match
        service = Service()

        key_name = ""
        key_type = ""

        if is_key_code:
            key_name = str(random.randint(0, 9999))
            key_type = str(random.randint(0, 9999))

        service.df_name = service_type + key_name
        service.df_type = service_type + key_type

        self.services.append(service)
        self.service_types.append(service_type)
        logger.info("Registry - Service Registered: " + service_type)

        return service
