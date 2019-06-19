import sys
import time

from pygomas.ontology import TEAM_AXIS, TEAM_ALLIED
from pygomas.bdisoldier import BDISoldier
from pygomas.bdimedic import BDIMedic
from pygomas.bdifieldop import BDIFieldOp
from pygomas.manager import Manager

# host = "localhost"
host = "gtirouter.dsic.upv.es"

manager_jid = "cmanager@" + host
service_jid = "cservice@" + host

axis_soldiers = list()
allied_soldiers = list()
axis_medics = list()
allied_medics = list()
axis_fieldops = list()
allied_fieldops = list()

# soldiers, fieldops, medics
num_axis = 3, 3, 3
num_allied = 3, 3, 3

print("Creating manager")
manager = Manager(players=sum(num_allied) + sum(num_axis),
                  # name=manager_jid, service_jid=service_jid, map_name="mine")
                  # name=manager_jid, service_jid=service_jid, map_name="mine_medium")
                  # name=manager_jid, service_jid=service_jid, map_name="mine_large")
                  name=manager_jid, service_jid=service_jid, map_name="map_01")
future = manager.start()
future.result()

# manager.container.loop.slow_callback_duration = 0.02

print("Creating soldiers")
for i in range(int(num_axis[0])):
  axis_soldiers.append(BDISoldier("axis_soldier{}@{}".format(i, host), "secret", 'pygomas/ASL/bditroop.asl', team=TEAM_AXIS, manager_jid=manager_jid, service_jid=service_jid))

for i in range(int(num_axis[1])):
  axis_fieldops.append(BDIFieldOp("axis_fieldops{}@{}".format(i, host), "secret", 'pygomas/ASL/fieldops.asl', team=TEAM_AXIS, manager_jid=manager_jid, service_jid=service_jid))

for i in range(int(num_axis[2])):
  axis_medics.append(BDIMedic("axis_medic{}@{}".format(i, host), "secret", 'pygomas/ASL/medic.asl', team=TEAM_AXIS, manager_jid=manager_jid, service_jid=service_jid))

for i in range(int(num_allied[0])):
  allied_soldiers.append(BDISoldier("allied_soldier{}@{}".format(i, host), "secret", asl='pygomas/ASL/bditroop.asl', team=TEAM_ALLIED, manager_jid=manager_jid, service_jid=service_jid))

for i in range(int(num_allied[1])):
  allied_fieldops.append(BDIFieldOp("allied_fieldops{}@{}".format(i, host), "secret", 'pygomas/ASL/fieldops.asl', team=TEAM_ALLIED, manager_jid=manager_jid, service_jid=service_jid))

for i in range(int(num_allied[2])):
  allied_medics.append(BDIMedic("allied_medic{}@{}".format(i, host), "secret", 'pygomas/ASL/medic.asl', team=TEAM_ALLIED, manager_jid=manager_jid, service_jid=service_jid))

port = 2000

for a in axis_soldiers + allied_soldiers + axis_medics + allied_medics + axis_fieldops + allied_fieldops:
  future = a.start()
  future.result()
  # a.web.start(hostname="localhost", port=port)
  # port += 1

while True:
  try:
    time.sleep(0.1)
  except KeyboardInterrupt:
    break
print("Exiting . . .")
from spade import quit_spade

quit_spade()
sys.exit(0)
