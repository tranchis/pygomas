#!/usr/bin/env python
# -*- coding: UTF8 -*-
import argparse
import socket
import sys
import os
import traceback


def main(address="localhost", port=8001, maps=None, log="/tmp/tv.log"):
    maps_path = maps

    f = open(log, "w")

    try:
        # Init socket
        s = None
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if s:
            s.connect((address, port))
            rfile = s.makefile('r', -1)
            wfile = s.makefile('w', 20)
            data = rfile.readline()

            wfile.write("READY\n")
            wfile.close()
            in_loop = True
            while in_loop:
                data = ""
                data = rfile.readline()
                if "COM" in data[0:5]:
                    if "Accepted" in data:
                        pass
                    elif "Closed" in data:
                        in_loop = False
                elif "MAP" in data[0:5]:
                    p = data.split()
                    map_name = p[2]
                    if maps_path is not None:
                        path = f"{maps_path}{os.sep}{map_name}{os.sep}{map_name}"
                    else:
                        this_dir, _ = os.path.split(__file__)
                        path = f"{this_dir}{os.sep}maps{os.sep}{map_name}{os.sep}{map_name}"
                    f.write(path)
                    f.write("\nSEP\n")
                elif "AGL" in data[0:5]:
                    f.write(data)
                    f.write("\nSEP\n")
                elif "TIM" in data[0:5]:
                    pass
                elif "ERR" in data[0:5]:
                    pass
                else:
                    # Unknown message type
                    pass

            # Close socket
            del rfile
            del wfile
            s.close()

    except Exception as e:
        print("Exception", str(e))
        print('-' * 60)
        traceback.print_exc(file=sys.stdout)
        print('-' * 60)

    finally:
        f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', default="localhost", help="Manager's address to connect the dumper")
    parser.add_argument('--port', default=8001, help="Manager's port to connect the dumper")
    parser.add_argument('--maps', default=None, help="The path to your custom maps directory")
    parser.add_argument('--log', default="/tmp/tv.log", help="File to save the game")

    args = parser.parse_args()

    main(args.ip, args.port, args.maps, args.log)
    sys.exit(0)
