from .bditroop import BDITroop, CLASS_SOLDIER
from .ontology import BACKUP_SERVICE


class BDISoldier(BDITroop):
    def __init__(self, actions=None, *args, **kwargs):
        soldier_actions = self.get_actions(actions=actions)
        super().__init__(actions=soldier_actions, *args, **kwargs)
        self.services.append(BACKUP_SERVICE)
        self.eclass = CLASS_SOLDIER
