import sys
import time

from pygomas.ontology import TEAM_AXIS, TEAM_ALLIED
from pygomas.soldier import Soldier
from pygomas.medic import Medic
from pygomas.fieldops import FieldOps
from pygomas.manager import Manager

import logging

# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger("spade.Agent").setLevel(logging.WARN)

host = "localhost"
host = "gtirouter.dsic.upv.es"

manager_jid = "cmanager@" + host
service_jid = "cservice@" + host

axis = list()
allied = list()

# soldiers, fieldops, medics
num_axis = 1, 0, 0
num_allied = 1, 0, 0

print("Creating manager")
manager = Manager(players=sum(num_allied) + sum(num_axis), name=manager_jid, service_jid=service_jid, map_name="map_01")
future = manager.start()
future.result()

# manager.container.loop.slow_callback_duration = 0.02
'''
print("Creating soldiers")
for i in range(int(num_axis[0])):
    axis.append(Soldier("axis_soldier{}@{}".format(i, host), "secret", team=TEAM_AXIS, manager_jid=manager_jid,
                        service_jid=service_jid))
for i in range(int(num_axis[1])):
    axis.append(FieldOps("axis_fieldops{}@{}".format(i, host), "secret", team=TEAM_AXIS, manager_jid=manager_jid,
                         service_jid=service_jid))
for i in range(int(num_axis[2])):
    axis.append(Medic("axis_medic{}@{}".format(i, host), "secret", team=TEAM_AXIS, manager_jid=manager_jid,
                      service_jid=service_jid))

for i in range(int(num_allied[0])):
    allied.append(Soldier("allied_soldier{}@{}".format(i, host), "secret", team=TEAM_ALLIED, manager_jid=manager_jid,
                          service_jid=service_jid))
for i in range(int(num_allied[1])):
    allied.append(FieldOps("allied_fieldops{}@{}".format(i, host), "secret", team=TEAM_ALLIED, manager_jid=manager_jid,
                           service_jid=service_jid))
for i in range(int(num_allied[2])):
    allied.append(Medic("allied_medic{}@{}".format(i, host), "secret", team=TEAM_ALLIED, manager_jid=manager_jid,
                        service_jid=service_jid))
'''
port = 2000
for a in axis + allied:
    a.start()
    # a.web.start(hostname="localhost", port=port)
    # port += 1
while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        break
print("Exiting . . .")
from spade import quit_spade

quit_spade()
sys.exit(0)
