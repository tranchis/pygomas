# -*- coding: utf-8 -*-

"""Console script for pygomas."""
import asyncio
import json
import os
import sys
import time
from importlib import import_module

import click

from spade import quit_spade
from spade.container import Container

from . import dump_battle
from . import replay_match
from . import canvasviewer
from . import textviewer
from .bdifieldop import BDIFieldOp
from .bdimedic import BDIMedic
from .bdisoldier import BDISoldier
from .manager import Manager, TEAM_AXIS, TEAM_ALLIED

help_config = json.dumps(
    {"host": "127.0.0.1", "manager": "cmanager", "service": "cservice",
     "axis": [{"rank": "BDISoldier", "name": "soldier_axis1", "password": "secret", "asl": "myASL/mybditroop.asl"},
              {"rank": "BDIMedic", "name": "medic_axis1", "password": "secret", "asl": "myASL/mymedic.asl"},
              {"rank": "BDIFieldOp", "name": "fieldops_axis1", "password": "secret", "asl": "myASL/myfieldops.asl"}],
     "allied": [
         {"rank": "mytroops.MySoldier", "name": "soldier_allied1", "password": "secret", "asl": "myASL/mybditroop.asl"},
         {"rank": "mytroops.MyMedic", "name": "medic_allied1", "password": "secret", "asl": "myASL/mymedic.asl"},
         {"rank": "mytroops.MyFieldOp", "name": "fieldops_allied1", "password": "secret", "amount": 2,
          "asl": "myASL/myfieldops.asl"}]
     },
    indent=4)


@click.group()
def cli():
    pass


@cli.command()
@click.option('-j', "--jid", default="cmanager@127.0.0.1", help="XMPP manager's JID (default=cmanager@127.0.0.1).")
@click.option('-p', "--password", default="secret", help="Manager's password (default=secret).")
@click.option('-np', "--num-players", help="Number of players (required).", required=True, type=int)
@click.option('-m', "--map", "map_name", default="map_01", help="Map name (default=map_01).")
@click.option('-mp', "--map-path", "map_path", default=None, help="The path to your custom maps directory.")
@click.option('-sj', "--service-jid", default="cservice@127.0.0.1",
              help="XMPP Service agent's JID (default=cservice@127.0.0.1).")
@click.option('-sp', "--service-password", default="secret", help="Service agent's password (default=secret).")
@click.option('-t', "--match-time", default=360, help="Max time in seconds for a match (default=360).", type=int)
@click.option("--fps", default=0.033, help="Frame rate in seconds per frame to inform renders (default=0.033).",
              type=float)
@click.option("--port", default=8001, help="Port to connect with renders (default=8001).", type=int)
def manager(jid, password, num_players, map_name, map_path, service_jid, service_password, match_time, fps, port):
    """Run the manager which controls the game."""
    click.echo("Running manager agent {}".format(jid))

    manager_agent = Manager(players=int(num_players), name=jid, passwd=password, map_name=map_name, map_path=map_path,
                            service_jid=service_jid, service_passwd=service_password,
                            match_time=match_time, fps=fps, port=port)
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
@click.option("-g", "--game", help="JSON file with game config (pygomas help run to get a sample)",
              type=click.Path(exists=True))
@click.option('-mp', "--map-path", "map_path", default=None, help="The path to your custom maps directory.")
def run(game, map_path):
    """Run a JSON game file with the players definition."""
    try:
        with open(game) as f:
            config = json.load(f)
    except json.decoder.JSONDecodeError:
        click.echo("{} must be a valid JSON file. Run pygomas help run to see an example.".format(game))
        return -1

    default = {
        "host": "127.0.0.1",
        "manager": "cmanager",
        "service": "cservice",
        "axis": [],
        "allied": []
    }
    for key in default.keys():
        if key not in config:
            config[key] = default[key]

    host = config["host"]
    manager_jid = "{}@{}".format(config["manager"], host)
    service_jid = "{}@{}".format(config["service"], host)

    troops = list()

    for troop in config["axis"]:
        new_troops = create_troops(troop, host, manager_jid, service_jid, map_path, team=TEAM_AXIS)
        troops += new_troops

    for troop in config["allied"]:
        new_troops = create_troops(troop, host, manager_jid, service_jid, map_path, team=TEAM_ALLIED)
        troops += new_troops

    container = Container()
    while not container.loop.is_running():
        time.sleep(0.1)

    futures = asyncio.run_coroutine_threadsafe(run_agents(troops), container.loop)
    futures.result()

    while any([agent.is_alive() for agent in troops]):
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    click.echo("Stopping troops . . .")

    quit_spade()

    return 0


def create_troops(troop, host, manager_jid, service_jid, map_path, team):
    this_dir, _ = os.path.split(__file__)
    asl_path = f"{this_dir}{os.sep}ASL{os.sep}"
    asl = {
        "BDISoldier": asl_path + 'bdisoldier.asl',
        "BDIMedic": asl_path + 'bdimedic.asl',
        "BDIFieldOp": asl_path + 'bdifieldop.asl'
    }
    assert "rank" in troop, "You must provide a rank for every troop"
    assert "name" in troop, "You must provide a name for every troop"
    assert "password" in troop, "You must provide a password for every troop"

    amount = troop["amount"] if "amount" in troop else 1
    new_troops = list()
    _class = load_class(troop["rank"])
    for i in range(amount):
        jid = "{}_{}@{}".format(troop["name"], i, host)
        try:
            agent_asl = troop["asl"] if "asl" in troop else asl[troop["rank"]]
        except KeyError:
            click.secho(f"No valid ASL file provided for agent {troop['name']}", fg="red", err=True)
            raise click.Abort()

        new_troop = _class(jid=jid, passwd=troop["password"], asl=agent_asl, team=team, map_path=map_path,
                           manager_jid=manager_jid, service_jid=service_jid)
        new_troops.append(new_troop)
    return new_troops


@cli.command()
@click.option("--ip", default="localhost", help="Manager's address to connect the render (default=localhost).",
              type=str)
@click.option("--port", default=8001, help="Manager's port to connect the render (default=8001).", type=int)
@click.option('--maps', default=None, help="The path to your custom maps directory.")
@click.option('--text', is_flag=True, help="Use the curses text render.")
def render(ip, port, maps, text):
    """Show the render to visualize a game."""
    if text:
        textviewer.main(address=ip, port=port, maps=maps)
    else:
        canvasviewer.main(address=ip, port=port, maps=maps)


@cli.command()
@click.option("--ip", default="localhost", help="Manager's address to connect the dumper (default=localhost).",
              type=str)
@click.option("--port", default=8001, help="Manager's port to connect the dumper (default=8001).", type=int)
@click.option('--log', default="/tmp/tv.log", help="File to save the game.")
def dump(ip, port, log):
    """Dump a game play to a file, in order to be replayed later."""
    dump_battle.main(address=ip, port=port, log=log)


@cli.command()
@click.option("-g", "--game", help="The file that contains the battle to visualize.", type=click.Path(exists=True))
@click.option('-f', "--fps", default=0.033, help="Frame rate speed to replay the game in seconds per frame.", type=float)
@click.option('--maps', default=None, help="The path to your custom maps directory.")
def replay(game, fps, maps):
    """Replay a game play from a file."""
    replay_match.main(game_file=game, fps=fps, maps_path=maps)


@cli.command()
@click.argument('subcommand')
@click.pass_context
def help(ctx, subcommand):
    """Show help about the other commands."""
    subcommand_obj = cli.get_command(ctx, subcommand)
    if subcommand_obj is None:
        click.echo("I don't know that command.")
    elif subcommand == "run":
        click.echo(subcommand_obj.get_help(ctx))
        click.echo("Game config JSON example: ")
        click.echo(help_config)
    else:
        click.echo(subcommand_obj.get_help(ctx))


async def run_agents(troops):
    coros = [agent.start() for agent in troops]
    return await asyncio.gather(*coros)


def load_class(class_path):
    """
    Tricky method that imports a class form a string.
    Args:
        class_path (str): the path where the class to be imported is.
    Returns:
        class: the class imported and ready to be instantiated.
    """
    ranks = {
        "BDISoldier": BDISoldier,
        "BDIMedic": BDIMedic,
        "BDIFieldOp": BDIFieldOp
    }

    if class_path in ranks:
        return ranks[class_path]
    else:
        sys.path.append(os.getcwd())
        module_path, class_name = class_path.rsplit(".", 1)
        mod = import_module(module_path)
        return getattr(mod, class_name)


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
