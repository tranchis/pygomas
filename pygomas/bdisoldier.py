from collections import deque

from .vector import Vector3D
from .bditroop import BDITroop, CLASS_SOLDIER
from .config import BACKUP_SERVICE, DESTINATION, VELOCITY, HEADING

from agentspeak import Actions
from agentspeak import grounded
from agentspeak.stdlib import actions as asp_action


class BDISoldier(BDITroop):

    def __init__(self, *args, **kwargs):
        soldier_actions = Actions(asp_action)

        @soldier_actions.add(".reinforce", 3)
        def _reinforce(agent, term, intention):
            """Same as a .goto"""
            args = grounded(term.args, intention.scope)
            self.movement.destination.x = args[0]
            self.movement.destination.y = args[1]
            self.movement.destination.z = args[2]
            start = (self.movement.position.x, self.movement.position.z)
            end = (self.movement.destination.x, self.movement.destination.z)
            path = self.path_finder.get_path(start, end)
            if path:
                self.destinations = deque(path)
                x, z = path[0]
                self.movement.calculate_new_orientation(Vector3D(x=x, y=0, z=z))
                self.bdi.set_belief(DESTINATION, args[0], args[1], args[2])
                self.bdi.set_belief(VELOCITY, self.movement.velocity.x, self.movement.velocity.y,
                                    self.movement.velocity.z)
                self.bdi.set_belief(HEADING, self.movement.heading.x, self.movement.heading.y, self.movement.heading.z)
            else:
                self.destinations = deque()
                self.movement.destination.x = self.movement.position.x
                self.movement.destination.y = self.movement.position.y
                self.movement.destination.z = self.movement.position.z
            yield

        super().__init__(actions=soldier_actions, *args, **kwargs)
        self.services.append(BACKUP_SERVICE)
        self.eclass = CLASS_SOLDIER
