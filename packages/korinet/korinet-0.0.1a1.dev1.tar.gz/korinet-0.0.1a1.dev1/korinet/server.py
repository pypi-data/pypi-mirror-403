import socket
import korinet
class server:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.client = korinet.protocol.v2(sock)

    def send(self, data: dict):
        self.client.send(data)
        if self.client.recv()["statusP"] != True:
            raise
    
    def recv(self, giveID: bool = False):
        data = self.client.recv(giveID)
        self.client.send({"statusP": True})
        return data
        # data = self.session.recv()
        # if data["type"] == "reconnect":
        #     pass
        # elif data["type"] == "new":
        #     pass


if __name__ == "__main__": # 1 client MAX
    import time
    import traceback

    # SOCKET
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 1235))
    sock.listen(10)
    sock.settimeout(5)
    lastBlocID = None
    try:
        while True:
            try:
                conn, addr = sock.accept()
                client = server(conn)
                while True:
                    print(client.recv(giveID=True))
                    client.send({"status": True})
                    time.sleep(1)
            except Exception as e:
                print(traceback.format_exc())
                print(e)
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    # PROTOCOL
    #session = server(sock)