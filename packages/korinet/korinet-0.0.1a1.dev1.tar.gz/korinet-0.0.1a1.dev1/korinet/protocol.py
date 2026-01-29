import time
import cbor2
import socket
import struct
import secrets
import threading

from functools import wraps
from datetime import datetime, timezone

class errors:
    class BlockSizeTooLarge(Exception): pass
    class BlockSizeTooLargeOnStream(Exception): pass
    class SocketRecvNone(Exception): pass

class v2:
    def __init__(self, sock: socket.socket, maxSizeBuffer: int = int(0.5 * 1024 *1024)): # 0.5 MB # 0.5 * 1024 *1024
        """
        Cette version du protocole est physiquement limitée a ce que chaque bloc ne dépasse pas 4 Go.
        """
        self.sock = sock
        self.debug = False
        # self.buffer = b""
        self.lock = threading.RLock() # RLock # Lock
        self.lockRecv = threading.RLock()
        self.lockSend = threading.RLock()
        self.maxSizeBuffer = maxSizeBuffer
    
    def _id(self, size: int = 16):
        return secrets.token_hex(size)

    def _wrapperStream(func):
        def wrapper(*args, **kwargs):
            gen = func(*args, **kwargs)
            next(gen)
            return gen
        return wrapper


    def _wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.monotonic_ns()
            result = func(*args, **kwargs)
            end_time = time.monotonic_ns()
            duration_ms = (end_time - start_time) / 1_000_000
            print(f"[Ping] {func.__name__}: {duration_ms:.3f} ms")
            return result
        return wrapper

    def _encodeInt(self, value: int) -> bytes: # I == 4 Go # 4 bytes
        return struct.pack("!I", value)
    
    def _decodeInt(self, value: bytes) -> int:
        return struct.unpack("!I", value)[0]
    
    def _send(self, obj: dict):
        if self.debug:
            print(f"Sending: {str(obj)[:256]}")
        payload = {"data": obj, "id": self._id()}  # received # "datetime": datetime.now(timezone.utc)
        payload = cbor2.dumps(payload)
        #print(f"Payload size: {len(payload)} bytes")
        size = self._encodeInt(len(payload))
        with self.lockSend:
            self.sock.sendall(size + payload) # msgpack.packb(data)

    def _recvall(self, size: int) -> bytes:
        with self.lockRecv:
            buffer = b""
            while True:
                data = self.sock.recv(size - len(buffer))
                if not data:
                    raise errors.SocketRecvNone()
                buffer += data
                if len(buffer) == size:
                    break
            return buffer
    
    def _recv(self, giveID: bool = False) -> dict:
        if self.debug:
            print("Waiting to receive data...")
        dataSize = self._decodeInt(self._recvall(4))
        if dataSize > self.maxSizeBuffer:
            raise errors.BlockSizeTooLarge(f"71 : BUFFER OVERFLOW : data size > maxSizeBuffer, received size_data: {dataSize}, maxSizeBuffer: {self.maxSizeBuffer}")
        dataRaw = self._recvall(dataSize)
        entry: dict = cbor2.loads(dataRaw)
        data = entry["data"]
        data["id"] = entry["id"]
        return data

    
    def recv(self, giveID: bool = False):
        return self._recv(giveID)

    def send(self, obj: dict):
        self._send(obj)

if __name__ == "__main__":
    session = v2(sock) # type: ignore
    session.send({"type": "ping"})
    if session.recv()["status"] != True:
        raise