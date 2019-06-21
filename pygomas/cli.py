# -*- coding: utf-8 -*-

"""Console script for pygomas."""
import asyncio
import json
import sys
import time
from typing import List, Union

import click

from spade import quit_spade
from spade.container import Container

from .bdifieldop import BDIFieldOp
from .bdimedic import BDIMedic
from .bdisoldier import BDISoldier
from .manager import Manager, TEAM_AXIS, TEAM_ALLIED

help_config = json.dumps(
    {"host": "127.0.0.1", "manager": "cmanager", "manager_password": "secret", "service": "cservice",
     "service_password": "secret",
     "axis": [{"rank": "soldier", "name": "soldier_axis1", "password": "secret", "asl": "pygomas/ASL/bditroop.asl"},
              {"rank": "medic", "name": "medic_axis1", "password": "secret", "asl": "pygomas/ASL/medic.asl"},
              {"rank": "fieldop", "name": "fieldops_axis1", "password": "secret", "asl": "pygomas/ASL/fieldops.asl"}],
     "allied": [{"rank": "soldier", "name": "soldier_allied1", "password": "secret", "asl": "pygomas/ASL/bditroop.asl"},
                {"rank": "medic", "name": "medic_allied1", "password": "secret", "asl": "pygomas/ASL/medic.asl"},
                {"rank": "fieldop", "name": "fieldops_allied1", "password": "secret", "asl": "pygomas/ASL/fieldops.asl"}]
     },
    indent=4)


@click.group()
def cli():
    pass


@cli.command()
@click.option('-j', "--jid", default="cmanager@127.0.0.1", help="XMPP manager's JID.")
@click.option('-p', "--password", default="secret", help="Manager's password.")
@click.option('-np', "--num-players", help="Number of players.", required=True, type=int)
@click.option('-m', "--map", "map_name", default="map_01", help="Map name.")
@click.option('-sj', "--service-jid", default="cservice@127.0.0.1", help="XMPP Service agent's JID.")
@click.option('-sp', "--service-password", default="secret", help="Service agent's password.")
def manager(jid, password, num_players, map_name, service_jid, service_password):
    """Console script for running the manager."""
    click.echo("Running manager agent {}".format(jid))

    manager_agent = Manager(players=int(num_players), name=jid, passwd=password, map_name=map_name,
                            service_jid=service_jid, service_passwd=service_password)
    future = manager_agent.start()
    future.result()

    while manager_agent.is_alive():
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
    click.echo("Stopping manager . . .")
    manager_agent.stop()

    quit_spade()

    return 0


@cli.command()
@click.option("-g", "--game", help="JSON file with game config", type=click.Path(exists=True))
def run(game):
    """Console script for running a JSON game file."""
    try:
        with open(game) as f:
            config = json.load(f)
    except json.decoder.JSONDecodeError:
        click.echo("{} must be a valid JSON file. Run pygomas help run to see an example.".format(game))
        return -1

    default = {
        "host": "127.0.0.1",
        "manager": "cmanager",
        "manager_password": "secret",
        "service": "cservice",
        "service_password": "secret",
        "axis": [],
        "allied": []
    }
    for key in default.keys():
        if key not in config:
            config[key] = default[key]

    host = config["host"]
    manager_jid = "{}@{}".format(config["manager"], host)
    service_jid = "{}@{}".format(config["service"], host)

    ranks = {
        "soldier": BDISoldier,
        "medic": BDIMedic,
        "fieldop": BDIFieldOp
    }

    asl = {
        "soldier": 'pygomas/ASL/bditroop.asl',
        "medic": 'pygomas/ASL/bdimedic.asl',
        "fieldop": 'pygomas/ASL/bdifieldop.asl'
    }

    troops: List[Union[BDIMedic, BDIFieldOp, BDISoldier]] = list()

    for troop in config["axis"]:
        assert "rank" in troop, "You must provide a rank for every troop"
        assert "name" in troop, "You must provide a name for every troop"
        assert "password" in troop, "You must provide a password for every troop"

        assert troop["rank"] in ranks, "Rank must be one of: soldier, medic or fieldop"

        _class = ranks[troop["rank"]]
        jid = "{}@{}".format(troop["name"], host)
        asl = troop["asl"] if "asl" in troop else asl[troop["rank"]]

        troop = _class(jid=jid, passwd=troop["password"], asl=asl, team=TEAM_AXIS,
                       manager_jid=manager_jid, service_jid=service_jid)

        future = troop.start()
        future.result()

        troops.append(troop)

    for troop in config["allied"]:
        assert "rank" in troop, "You must provide a rank for every troop"
        assert "name" in troop, "You must provide a name for every troop"
        assert "password" in troop, "You must provide a password for every troop"

        assert troop["rank"] in ranks, "Rank must be one of: soldier, medic or fieldop"

        _class = ranks[troop["rank"]]
        jid = "{}@{}".format(troop["name"], host)
        asl = troop["asl"] if "asl" in troop else asl[troop["rank"]]

        troop = _class(jid=jid, passwd=troop["password"], asl=asl, team=TEAM_ALLIED,
                       manager_jid=manager_jid, service_jid=service_jid)

        future = troop.start()
        future.result()

        troops.append(troop)

    container = Container()
    while not container.loop.is_running():
        time.sleep(0.1)
    coros = [agent._async_start() for agent in troops]
    future = asyncio.run_coroutine_threadsafe(run_agents(coros), container.loop)
    future.result()

    while any([agent.is_alive() for agent in troops]):
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    click.echo("Stopping troops . . .")

    quit_spade()

    return 0


@cli.command()
@click.argument('subcommand')
@click.pass_context
def help(ctx, subcommand):
    subcommand_obj = cli.get_command(ctx, subcommand)
    if subcommand_obj is None:
        click.echo("I don't know that command.")
    elif subcommand == "run":
        click.echo(subcommand_obj.get_help(ctx))
        click.echo("Game config JSON example: ")
        click.echo(help_config)
    else:
        click.echo(subcommand_obj.get_help(ctx))


async def run_agents(agents):
    await asyncio.gather(*agents)


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
