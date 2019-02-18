import sys
import time
from pygomas.CTroop import CTroop
from pygomas.CSoldier import CSoldier
from pygomas.CMedic import CMedic
from pygomas.CFieldOps import CFieldOps
from pygomas.CManager import CManager


host = "gtirouter.dsic.upv.es"

axis = list()
allied = list()

manager = CManager(players=2)
manager.start()

axis.append( CSoldier("x0@"+host, "secret", team=CTroop.TEAM_AXIS) )
#axis.append( CSoldier("x1@"+host, "secret", team=Troop.TEAM_AXIS) )
#axis.append( CSoldier("x2@"+host, "secret", team=Troop.TEAM_AXIS) )
#axis.append( CFieldOps("x3@"+host, "secret", team=Troop.TEAM_AXIS) )
#axis.append( CFieldOps("x4@"+host, "secret", team=Troop.TEAM_AXIS) )
#axis.append( CMedic("x5@"+host, "secret", team=Troop.TEAM_AXIS) )
#axis.append( CMedic("x6@"+host, "secret", team=Troop.TEAM_AXIS) )
#axis.append( CMedic("x7@"+host, "secret", team=Troop.TEAM_AXIS) )

allied.append( CSoldier("a0@"+host, "secret", team=CTroop.TEAM_ALLIED) )
#allied.append( CSoldier("a1@"+host, "secret", team=Troop.TEAM_ALLIED) )
#allied.append( CSoldier("a2@"+host, "secret", team=Troop.TEAM_ALLIED) )
#allied.append( CFieldOps("a3@"+host, "secret", team=Troop.TEAM_ALLIED) )
#allied.append( CFieldOps("a4@"+host, "secret", team=Troop.TEAM_ALLIED) )
#allied.append( CMedic("a5@"+host, "secret", team=Troop.TEAM_ALLIED) )
#allied.append( CMedic("a6@"+host, "secret", team=Troop.TEAM_ALLIED) )
#allied.append( CMedic("a7@"+host, "secret", team=Troop.TEAM_ALLIED) )

for a in axis + allied: a.start()
while True:
    try:
        time.sleep(1)
    except:
        print ("Stopping agents . . .")
        for a in axis + allied: a.stop()
        print ("done")
        break
manager.stop()

print ("Exiting . . .")
sys.exit(0)
