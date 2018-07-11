import threading
import socketserver
import time
import _thread


class CServer(threading.Thread):
    SERVER_PORT = 8072  # our server's own port

    class CRequestHandler(socketserver.StreamRequestHandler):
        TCP_COM = 0  # COMMUNICATION (ACCEPTED, CLOSED, REFUSED)
        TCP_AGL = 1  # AGENT LIST
        TCP_MAP = 2  # MAP: NAME, CHANGES, etc.
        TCP_TIME = 3  # TIME: LEFT TIME

        def __init__(self, request, client_address, server):
            self.synchronizer = _thread.allocate_lock()
            socketserver.StreamRequestHandler.__init__(self, request, client_address, server)

        def SendMsgToRenderEngine(self, _msgType, _msg):
            self.synchronizer.acquire()
            sMsgToSend = ""

            if _msgType == self.TCP_COM:
                sMsgToSend = "COM "
            elif _msgType == self.TCP_AGL:
                sMsgToSend = "AGL "
            elif _msgType == self.TCP_MAP:
                sMsgToSend = "MAP "
            elif _msgType == self.TCP_TIME:
                sMsgToSend = "TIME "
            else:
                sMsgToSend = "ERR "

            sMsgToSend += _msg + "\n"

            try:
                # self.wfile.flush()
                self.wfile.write(bytes(sMsgToSend, encoding="UTF-8"))
                # self.wfile.flush()
                # print "CServer: Sent message #"+ str(sMsgToSend) + "# to client"
            except:
                print("EXCEPTION IN SENDMSGTORE")

            self.synchronizer.release()

        def handle(self):
            # Type of Message to Send:
            self.TCP_COM = 0  # COMMUNICATION (ACCEPTED, CLOSED, REFUSED)
            self.TCP_AGL = 1  # AGENT LIST
            self.TCP_MAP = 2  # MAP: NAME, CHANGES, etc.
            self.TCP_TIME = 3  # TIME: LEFT TIME

            self.m_sMapName = self.server.m_sMapName

            # m_Socket = socket;
            print("Preparing Connection to " + str(self.client_address))  # + ":" + str(self.request)

            try:
                self.wfile.write(bytes("JGOMAS Render Engine Server v. 0.1.0, " + time.asctime() + '\n', encoding="UTF-8"))
                print("JGOMAS Render Engine Server v. 0.1.0")
                # self.wfile.flush()
                # m_sMapName = _sMapName;
            except Exception as e:
                print(str(e))

            sClientRequest = ""
            bExit = False
            print("Waiting for client")
            while not bExit:
                try:
                    # self.synchronizer.acquire()
                    sClientRequest = self.rfile.readline()
                    # self.synchronizer.release()
                    print("Client says:" + str(sClientRequest))
                    sClientRequest = str(sClientRequest)
                    if "READY" in sClientRequest:
                        print("Server: Connection Accepted")
                        self.SendMsgToRenderEngine(self.TCP_COM, "Server: Connection Accepted ")
                        # time.sleep(0.250)  # let's try the buffer be flushed
                        self.SendMsgToRenderEngine(self.TCP_MAP, "NAME: " + self.m_sMapName + "  ")
                        # time.sleep(0.250)  # let's try the buffer be flushed
                        self.server.m_ConnectionList.append(self)

                    if "MAPNAME" in sClientRequest:
                        print("Server: Client requested mapname")
                        self.SendMsgToRenderEngine(self.TCP_MAP, "NAME: " + self.m_sMapName + "  ")

                    if "QUIT" in sClientRequest:
                        print("Server: Client quitted")
                        self.server.m_ConnectionList.remove(self)
                        self.SendMsgToRenderEngine(self.TCP_COM, "Server: Connection Closed")
                        bExit = True
                    else:
                        # Close connection
                        time.sleep(0.05)

                except Exception as e:
                    print("EXCEPTION:", str(e))
                    bExit = True

            if self in self.server.m_ConnectionList:
                self.server.m_ConnectionList.remove(self)
                print("Server: Connection closed")

    def __init__(self, _sMapName):
        threading.Thread.__init__(self)
        self.m_ConnectionList = []
        self.m_sMapName = _sMapName
        self.m_bExit = False

    def run(self):
        print("JGOMAS CServer running ...")
        self.server = None

        # Create service
        try:
            socketserver.ThreadingTCPServer.allow_reuse_address = True
            self.server = socketserver.ThreadingTCPServer(("", self.SERVER_PORT), self.CRequestHandler)
        except Exception as e:
            print(str(e))

        if self.server:
            self.server.synchronizer = _thread.allocate_lock()
            self.server.m_sMapName = self.m_sMapName
            self.server.m_ConnectionList = self.m_ConnectionList
            try:
                self.server.serve_forever()
            except:
                print("Shutting down server")

