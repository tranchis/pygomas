#!/usr/bin/env python
# -*- coding: UTF8 -*-
import argparse
import json
import socket
import sys
import os
import traceback
import copy
import pygame
from pygame import gfxdraw
import curses
import math
from loguru import logger


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


class Render(object):

    def __init__(self, address="localhost", port=8001, maps=None, text=False):
        self.address = address
        self.port = port
        self.maps_path = maps
        self.text = text
        self.s = None
        self.screen = None
        self.font = None
        self.maps_path = None

        self.objective_x = -1
        self.objective_y = -1
        self.allied_base = None
        self.axis_base = None
        self.graph = {}
        self.agents = {}
        self.dins = {}
        self.factor = 2

        self.iteration = 0

        self.tile_size = 24
        self.horizontal_tiles = 32
        self.vertical_tiles = 32

        self.map_width = self.tile_size * self.horizontal_tiles
        self.map_height = self.tile_size * self.vertical_tiles

        self.xdesp = 0
        self.ydesp = 0
        self.size = [self.map_width, self.map_height]

        self.show_fovs = True
        self.quit = False

    def main(self):
        if self.text:
            curses.wrapper(self._main)
        else:
            self._main()

    def _main(self, stdscr=None):
        error = False
        if not self.text:
            # Init pygame
            pygame.init()
            self.font = pygame.font.SysFont("ttf-font-awesome", 12)

            # Set the height and width of the self.screen
            self.screen = pygame.display.set_mode(self.size)

        else:
            stdscr = curses.initscr()
            curses.start_color()
            curses.noecho()
            curses.cbreak()
            stdscr.keypad(1)

        try:
            # Init socket
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.s:
                self.s.connect((self.address, self.port))
                rfile = self.s.makefile('r', -1)
                wfile = self.s.makefile('w', 20)
                data = rfile.readline()

                wfile.write("READY\n")
                wfile.close()
                while not self.quit:
                    data = ""
                    data = rfile.readline()
                    if "COM" in data[0:5]:
                        if "Accepted" in data:
                            pass
                        elif "Closed" in data:
                            self.quit = True
                    elif "MAP" in data[0:5]:
                        p = data.split()
                        mapname = p[2]
                        result = self.load_map(mapname)
                        if result["status"] != "ok":
                            error = result["value"]
                            self.quit = True
                    elif "AGL" in data[0:5]:
                        self.agl_parse(data)
                    elif "TIM" in data[0:5]:
                        pass
                    elif "ERR" in data[0:5]:
                        pass
                    else:
                        # Unknown message type
                        pass
                    if not self.text:
                        self.draw()
                    else:
                        self.textdraw(stdscr)

        except Exception as e:
            tb = traceback.extract_stack()
            error = str(e) + "\n" + "\n".join([repr(i) for i in tb])

        finally:
            logger.info("Closing...")
            # Close socket
            self.s.close()
            if not self.text:
                pygame.quit()
            else:
                curses.nocbreak()
                # self.stdscr.keypad(False)
                curses.echo()
                curses.endwin()

            if error:
                logger.error('-' * 60)
                logger.error(str(error))
                logger.error('-' * 60)

    def agl_parse(self, data):
        self.dins = {}
        agl = data.split()
        nagents = int(agl[1])
        agl = agl[2:]
        separator = nagents * 15
        agent_data = agl[:separator]
        din_data = agl[separator:]
        for i in range(nagents):
            self.agents[agent_data[0]] = {"type": agent_data[1], "team": agent_data[2], "health": agent_data[3],
                                          "ammo": agent_data[4], "carrying": agent_data[5],
                                          "posx": agent_data[6].strip("(,)"), "posy": agent_data[7].strip("(,)"),
                                          "posz": agent_data[8].strip("(,)"),
                                          "angx": agent_data[12].strip("(,)"), "angy": agent_data[13].strip("(,)"),
                                          "angz": agent_data[14].strip("(,)")}
            agent_data = agent_data[15:]

        ndin = int(din_data[0])
        din_data = din_data[1:]
        for din in range(ndin):
            self.dins[din_data[0]] = {"type": din_data[1], "posx": din_data[2].strip("(,)"),
                                      "posy": din_data[3].strip("(,)"),
                                      "posz": din_data[4].strip("(,)")}
            din_data = din_data[5:]

    def draw(self):

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.xdesp += self.tile_size
                elif event.key == pygame.K_RIGHT:
                    self.xdesp -= self.tile_size
                elif event.key == pygame.K_DOWN:
                    self.ydesp -= self.tile_size
                elif event.key == pygame.K_UP:
                    self.ydesp += self.tile_size
                elif event.key == pygame.K_x:
                    self.tile_size += 2
                elif event.key == pygame.K_z:
                    self.tile_size -= 2
                elif event.key == pygame.K_f:
                    self.show_fovs = not self.show_fovs
            elif event.type == pygame.QUIT:
                self.quit = True

        # Clear screen
        color_background = (0, 0, 0)
        pygame.draw.rect(self.screen, color_background, (0, 0, self.map_width, self.map_height))

        # Draw Map
        color_wall = (100, 100, 100)
        for y in range(0, len(list(self.graph.items()))):
            for x in range(0, 32):
                try:
                    if list(self.graph.items())[y][1][x] == '*':
                        pygame.draw.rect(self.screen, color_wall,
                                         (x * self.tile_size + self.xdesp,
                                          y * self.tile_size + self.ydesp,
                                          self.tile_size, self.tile_size))
                except:
                    pass

        # Draw bases
        if self.allied_base is not None:
            color = (255, 0, 0)
            xpos = int(self.allied_base[0]) * self.tile_size + self.xdesp
            ypos = int(self.allied_base[1]) * self.tile_size + self.ydesp
            xwidth = int(self.allied_base[2]) * self.tile_size - xpos + self.tile_size + self.xdesp
            ywidth = int(self.allied_base[3]) * self.tile_size - ypos + self.tile_size + self.ydesp

            pygame.draw.rect(self.screen, color, (xpos, ypos, xwidth, ywidth))

        if self.axis_base is not None:
            color = (0, 0, 255)
            xpos = int(self.axis_base[0]) * self.tile_size + self.xdesp
            ypos = int(self.axis_base[1]) * self.tile_size + self.ydesp
            xwidth = int(self.axis_base[2]) * self.tile_size - xpos + self.tile_size + self.xdesp
            ywidth = int(self.axis_base[3]) * self.tile_size - ypos + self.tile_size + self.ydesp

            pygame.draw.rect(self.screen, color, (xpos, ypos, xwidth, ywidth))

        # Draw items
        for i in range(0, len(list(self.dins.items()))):
            posx = int(float(list(self.dins.items())[i][1]['posx']) * (self.tile_size / 8.0)) + self.xdesp
            posy = int(float(list(self.dins.items())[i][1]['posz']) * (self.tile_size / 8.0)) + self.ydesp

            item_type = {
                "1001": "M",
                "1002": "A",
                "1003": "F"
            }.get(list(self.dins.items())[i][1]["type"], "X")

            color = {
                "1001": (255, 255, 255),
                "1002": (255, 255, 255),
                "1003": (255, 255, 0)
            }.get(list(self.dins.items())[i][1]["type"], "X")

            pygame.draw.circle(self.screen, color, [posx, posy], 6)
            text = self.font.render(item_type, True, (0, 0, 0))
            self.screen.blit(text, (posx - text.get_width() // 2, posy - text.get_height() // 2))

        # Draw units
        for i in list(self.agents.items()):
            health = float(i[1]['health'])

            if float(health) > 0:

                carrying = i[1]['carrying']

                agent_type = {
                    "0": "X",
                    "1": "*",
                    "2": "+",
                    "3": "Y",
                    "4": "^"
                }.get(i[1]['type'], "X")

                team = {
                    "100": (255, 100, 100),
                    "200": (100, 100, 255)
                }.get(i[1]['team'], (255, 255, 0))

                team_aplha = {
                    "100": (255, 100, 100, 100),
                    "200": (100, 100, 255, 100)
                }.get(i[1]['team'], (255, 255, 0, 255))

                ammo = float(i[1]['ammo'])

                posx = int(float(i[1]['posx']) * self.tile_size / 8.0) + self.xdesp
                posy = int(float(i[1]['posz']) * self.tile_size / 8.0) + self.ydesp

                # print avatar
                pygame.draw.circle(self.screen, team, [posx, posy], 8)
                # print name
                text = self.font.render(i[0], True, (255, 255, 255))
                self.screen.blit(text, (posx - text.get_width() // 2 + 15, posy - text.get_height() // 2 - 15))
                # print health
                pygame.gfxdraw.aacircle(self.screen, posx, posy, 10, (255, 0, 0))
                pygame.gfxdraw.aacircle(self.screen, posx, posy, 9, (255, 0, 0))
                pygame.gfxdraw.arc(self.screen, posx, posy, 10, 0, int(health * 3.6) - 1, (0, 255, 0))
                pygame.gfxdraw.arc(self.screen, posx, posy, 9, 0, int(health * 3.6) - 1, (0, 255, 0))
                # print ammo
                if ammo >= 1:
                    pygame.gfxdraw.arc(self.screen, posx, posy, 6, 0, int(ammo * 3.6) - 1, (255, 255, 255))
                    pygame.gfxdraw.arc(self.screen, posx, posy, 7, 0, int(ammo * 3.6) - 1, (255, 255, 255))

                # is carring flag?
                if carrying == '1':
                    pygame.draw.circle(self.screen, (255, 255, 0), [posx, posy], 5)

                # print fov
                if self.show_fovs:
                    # compute direction
                    angx = float(i[1]['angx'])
                    angy = float(i[1]['angz'])

                    if angx == 0:
                        div = 1000
                    else:
                        div = angy / angx

                    if angy >= 0 and angx >= 0:  # q1
                        angle = math.atan(div) * (180 / math.pi)
                    elif angy >= 0 >= angx:  # q2
                        angle = math.atan(div) * (180 / math.pi) + 180
                    elif angy <= 0 and angx <= 0:  # q3
                        angle = math.atan(div) * (180 / math.pi) + 180
                    else:  # q4
                        angle = math.atan(div) * (180 / math.pi) + 360

                    for j in range(0, int(48 * (self.tile_size / 8)), 1):
                        pygame.gfxdraw.arc(self.screen, posx, posy, j, int(-45 + angle), int(45 + angle), team_aplha)

                # print function
                text = self.font.render(agent_type, True, (0, 0, 0))
                self.screen.blit(text, (posx - text.get_width() // 2, posy - text.get_height() // 2))

        pygame.display.flip()
        self.iteration += 1

    def textdraw(self, stdscr):
        height, width = stdscr.getmaxyx()

        # Draw Map
        for k, v in list(self.graph.items()):
            try:
                newline = ""
                for char in v:
                    newline += char * self.factor
                if height > k:
                    stdscr.addstr(k, 0, str(newline))
            except:
                pass

        # Draw bases
        # ALLIED BASE
        if self.allied_base is not None:
            curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_RED)  # ALLIED BASE
            for y in range(int(self.allied_base[1]), int(self.allied_base[3])):
                for x in range(int(self.allied_base[0]) * self.factor, int(self.allied_base[2]) * self.factor):
                    if height > y:
                        stdscr.addstr(y, x, " ", curses.color_pair(4))

        # AXIS BASE
        if self.axis_base is not None:
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLUE)  # AXIS BASE
            for y in range(int(self.axis_base[1]), int(self.axis_base[3])):
                for x in range(int(self.axis_base[0]) * self.factor, int(self.axis_base[2]) * self.factor):
                    if height > y:
                        stdscr.addstr(y, x, " ", curses.color_pair(3))

        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        # PACKS
        for k, v in list(self.dins.items()):
            #  Type
            if v["type"] == "1001":
                c = "M"
            elif v["type"] == "1002":
                c = "A"
            elif v["type"] == "1003":
                c = "F"
            else:
                c = "X"
            y = int(float(v["posz"]) / 8)
            x = int(float(v["posx"]) / (8 / self.factor))
            if height > y:
                stdscr.addstr(y, x, c, curses.color_pair(2))

        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_RED)  # ALLIED
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)  # AXIS
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_WHITE)  #  OTHER / DEAD

        # AGENTS
        stats_allied = []  # ""
        stats_axis = []  # ""
        for k, v in list(self.agents.items()):
            # Type
            if v["type"] == "0":
                c = "X"
            elif v["type"] == "1":
                c = "*"
            elif v["type"] == "2":
                c = "+"
            elif v["type"] == "3":
                c = "Y"
            elif v["type"] == "4":
                c = "^"
            else:
                c = "X"
            # Team (or Carrier)
            if v["carrying"] == "1":
                t = 2
            elif v["team"] == "100":
                t = 5
            elif v["team"] == "200":
                t = 6
            else:
                t = 1
            # Draw in map
            y = int(float(v["posz"]) / 8)
            x = int(float(v["posx"]) / (8 / self.factor))
            if int(v["health"]) > 0:
                if height > y:
                    stdscr.addstr(y, x, c, curses.color_pair(t))  #  Alive
            else:
                if height > y:
                    stdscr.addstr(y, x, "D", curses.color_pair(7))  #  Dead
            # Write stats
            if v["team"] == "100":
                if int(v["health"]) > 0:
                    stats_allied.append(f" | {c} {k.ljust(4)} {int(v['health']):03d} {int(v['ammo']):03d} ")
                else:
                    stats_allied.append(f" | {c} {k.ljust(4)} --- --- ")
            elif v["team"] == "200":
                if int(v["health"]) > 0:
                    # stats_axis += " | %s %s %03d %03d " % (c, k, int(v["health"]), int(v["ammo"]))
                    stats_axis.append(f" | {c} {k.ljust(4)} {int(v['health']):03d} {int(v['ammo']):03d} ")
                else:
                    stats_axis.append(f" | {c} {k.ljust(4)} --- --- ")
        # blank = " " * 81
        # stdscr.addstr(33, 1, blank)
        row = 33
        for _agents in chunks(stats_allied, 4):
            line = "".join(_agents)
            if height > row:
                stdscr.addstr(row, 1, str(line), curses.color_pair(5))
            row += 1
        # stdscr.addstr(34, 1, blank)
        for _agents in chunks(stats_axis, 4):
            line = "".join(_agents)
            if height > row:
                stdscr.addstr(row, 1, str(line), curses.color_pair(6))
            row += 1

        # Refresh screen
        try:
            stdscr.refresh()
        except:
            pass

    def load_map(self, map_name):
        try:
            if self.maps_path is not None:
                path = f"{self.maps_path}{os.sep}{map_name}{os.sep}"
            else:
                this_dir, _ = os.path.split(__file__)
                path = f"{this_dir}{os.sep}maps{os.sep}{map_name}{os.sep}"

            if os.path.exists(f"{path}{map_name}.json"):
                with open(f"{path}{map_name}.json") as f:
                    mapf = json.load(f)
                    self.objective_x = int(mapf["objective"][0])
                    self.objective_y = int(mapf["objective"][1])
                    self.allied_base = mapf["spawn"]["allied"]
                    self.axis_base = mapf["spawn"]["axis"]
                    cost = open(f"{path}{mapf['cost_map']['file']}", "r")

            else:
                mapf = open(f"{path}{map_name}.txt", "r")
                cost = open(f"{path}{map_name}_cost.txt", "r")
                for line in mapf.readlines():
                    if "pGomas_OBJECTIVE" in line:
                        splitted_line = line.split()
                        self.objective_x = copy.copy(int(splitted_line[1]))
                        self.objective_y = copy.copy(int(splitted_line[2]))
                    elif "pGomas_SPAWN_ALLIED" in line:
                        splitted_line = line.split()
                        splitted_line.pop(0)
                        self.allied_base = copy.copy(splitted_line)
                    elif "pGomas_SPAWN_AXIS" in line:
                        splitted_line = line.split()
                        splitted_line.pop(0)
                        self.axis_base = copy.copy(splitted_line)
                mapf.close()

            y = 0
            for line in cost.readlines():
                self.graph[y] = line.strip("\r\n")
                y += 1
            cost.close()
            return {"status": "ok"}
        except Exception as e:
            tb = traceback.extract_stack()
            return {"status": "error", "value": str(e) + "\n" + "\n".join([repr(i) for i in tb])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', default="localhost", help="Manager's address to connect the render")
    parser.add_argument('--port', default=8001, help="Manager's port to connect the render")
    parser.add_argument('--maps', default=None, help="The path to your custom maps directory")
    parser.add_argument('--text', default=False, help="Use text render")

    args = parser.parse_args()
    render = Render(args.ip, args.port, args.maps, args.text)
    render.main()
    sys.exit(0)
