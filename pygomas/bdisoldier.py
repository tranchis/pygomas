from .bditroop import BDITroop, CLASS_SOLDIER
from .ontology import BACKUP_SERVICE


class BDISoldier(BDITroop):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.services.append(BACKUP_SERVICE)
        self.eclass = CLASS_SOLDIER
