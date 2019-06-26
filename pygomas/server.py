import asyncio
import time

from loguru import logger

from spade.container import Container

TCP_COM = 0  # COMMUNICATION (ACCEPTED, CLOSED, REFUSED)
TCP_AGL = 1  # AGENT LIST
TCP_MAP = 2  # MAP: NAME, CHANGES, etc.
TCP_TIME = 3  # TIME: LEFT TIME


class Server(object):
    def __init__(self, map_name, port=8001):
        self.clients = {}
        self.map_name = map_name
        self.port = port
        self.server = None

        self.container = Container()

        self.loop = self.container.loop

        self.coro = asyncio.start_server(self.accept_client, "", self.port, loop=self.loop)

    def get_connections(self):
        return self.clients.keys()

    def start(self):
        self.server = self.loop.create_task(self.coro)
        logger.info("Render Server started: {}".format(self.server))

    def stop(self):
        self.server.stop()
        self.loop.run_until_complete(self.server.wait_closed())

    def accept_client(self, client_reader, client_writer):
        logger.info("New Connection")
        task = asyncio.Task(self.handle_client(client_reader, client_writer))
        self.clients[task] = (client_reader, client_writer, False)

        def client_done(task_):
            del self.clients[task_]
            client_writer.close()
            logger.info("End Connection")

        task.add_done_callback(client_done)

    def is_ready(self, task):
        return self.clients[task][2]

    async def handle_client(self, reader, writer):
        task = None
        for k, v in self.clients.items():
            if v[0] == reader and v[1] == writer:
                task = k
                break
        # + ":" + str(self.request)
        logger.info("Preparing Connection to " + str(task))

        try:
            welcome_message = "JGOMAS Render Engine Server v. 0.1.0, {}\n".format(
                time.asctime()).encode("ASCII")
            writer.write(welcome_message)
            # await writer.drain()
            logger.info("JGOMAS Render Engine Server v. 0.1.0 (len={})".format(
                len(welcome_message)))
        except Exception as e:
            logger.info("EXCEPTION IN WELCOME MESSAGE")
            logger.info(str(e))

        while True:
            # data = await asyncio.wait_for(reader.readline(), timeout=10.0)
            data = await reader.readline()
            if data is None:
                logger.info("Received no data")
                print("Received no data")
                # exit echo loop and disconnect
                return
            # self.synchronizer.release()
            data = data.decode().rstrip()
            print("DATA", data)
            logger.info("Client says:" + data)
            if "READY" in data:
                logger.info("Server: Connection Accepted")
                self.send_msg_to_render_engine(
                    task, TCP_COM, "Server: Connection Accepted")
                self.send_msg_to_render_engine(
                    task, TCP_MAP, "NAME: " + self.map_name + " ")
                logger.info("Sending: NAME: " + self.map_name)

                self.clients[task] = (reader, writer, True)

            elif "MAPNAME" in data:
                logger.info("Server: Client requested mapname")
                self.send_msg_to_render_engine(
                    task, TCP_MAP, "NAME: " + self.map_name + " ")
                self.clients[task] = (reader, writer, True)

            elif "QUIT" in data:
                logger.info("Server: Client quitted")
                self.send_msg_to_render_engine(
                    task, TCP_COM, "Server: Connection Closed")
                return
            else:
                # Close connection
                logger.info("Socket closed, closing connection.")
                return

    def send_msg_to_render_engine(self, task, msg_type, msg):
        writer = None
        for k, v in self.clients.items():
            if k == task:
                writer = v[1]
                break
        if writer is None:
            logger.info("Connection for {task} not found".format(task=task))
            return
        type_dict = {TCP_COM: "COM", TCP_AGL: "AGL",
                     TCP_MAP: "MAP", TCP_TIME: "TIME"}

        msg_type = type_dict[msg_type] if msg_type in type_dict else "ERR"

        msg_to_send = "{} {}\n".format(msg_type, msg)

        try:
            writer.write(msg_to_send.encode("ASCII"))
        except Exception as e:
            logger.error("EXCEPTION IN SENDMSGTORE: {}".format(e))
