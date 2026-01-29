import time
import socket

import korinet

class errors:
    class Timeout(Exception): pass

class client:
    def __init__(self, address: str, port: int, timeout=120):
        self.address = address
        self.port = port
        self.timeout = timeout
        self.protocol = korinet.protocol.v2(sock=self._connect())
    
    def _connect(self):
        num = 0
        start_time = time.monotonic()
        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((self.address, self.port))
                print("ok")
                return sock
            except (socket.timeout, ConnectionRefusedError) as e:
                num += 1
                print(f"{num}/?, timeout=={self.timeout}")
                sock.close()
                if time.monotonic() - start_time >= self.timeout:
                    raise errors.Timeout() from e
                else:
                    time.sleep(1)
    
    def send(self, data: dict):
        while True:
            try:
                self.protocol.send(data)
                if self.protocol.recv()["statusP"] != True:
                    raise
                return True
            except (socket.error, korinet.protocol.errors.SocketRecvNone) as e:
                print("Erreur socket :", e)
                self.protocol.sock = self._connect()

    def recv(self):
        while True:
            try:
                data = self.protocol.recv()
                self.protocol.send({"statusP": True})
                return data
            except (socket.error, korinet.protocol.errors.SocketRecvNone) as e:
                print("Erreur socket :", e)
                self.protocol.sock = self._connect()

if __name__ == "__main__":
    C = client("127.0.0.1", 1235, timeout=4)
    num = 0
    while True:
        C.send({"type": "ping", "num": num})
        print(C.recv())
        num += 1
        time.sleep(1)