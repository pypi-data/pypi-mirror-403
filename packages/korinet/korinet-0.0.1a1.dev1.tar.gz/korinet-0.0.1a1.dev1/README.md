# KoriNet (Korixa Network Protocol)
A modern alternative for TCP communication—simple, fast, and secure. Designed to structure high-level data exchanges, KoriNet ensures reliability, integrity, and continuity. Lightweight and modular, it adapts to any type of application, from chat and audio to server management, providing developers with a robust and universal protocol.

## ⚠️ **Warning / Usage Limitations**

KoriNet is **not recommended for public production use**. Its current design, which ACKs every message, is **optimized for low-latency LANs** and **stable 24/7 infrastructures**. It is intended for **internal APIs and fixed applications**, not for video, high-latency networks, or heterogeneous clients.  

## ⚠️ **Important:** At the moment, there is **no version coordination**, so all clients must run the **exact same version** of KoriNet to ensure reliability. Future updates will add TLS 1.3 encryption and version management.  

Use KoriNet only in environments where **stability, low latency, and controlled network conditions** are guaranteed.


# 🔌 Connection resilience & reconnection handling

![Terminal Screenshot](./Assets/reconnect-0.png)

The following console capture illustrates how KoriNet behaves during a connection loss between a client and a server.

### **(1)** Client-side behavior

The client automatically detects the connection failure and continuously attempts to reconnect by creating new TCP sockets. This demonstrates KoriNet’s ability to recover from transient network errors without manual intervention.

### **(2)** Connection interruption

The disconnection is intentionally triggered using a KeyboardInterrupt on the server side. This simulates a real-world network failure (service crash, link loss, or network interruption) and produces the same behavior as an actual outage.

This example highlights KoriNet’s usefulness for long-running services (24/7), internal APIs, and stable infrastructures, where automatic reconnection and communication continuity are critical.

# Example (0.0.1a1.dev1)

For the latest examples, please refer to: [**here**](./tests/main.py), [**server**](./korinet/server.py), [**client**](./korinet/client.py).

## ☁️ Server
```python
import time
import traceback
from korinet import server

# SOCKET
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("127.0.0.1", 1235))
sock.listen(10)
sock.settimeout(5)
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
```

## 👤 Client
```python
from korinet import client
C = client("127.0.0.1", 1235, timeout=4)
num = 0
while True:
    C.send({"type": "ping", "num": num})
    print(C.recv())
    num += 1
    time.sleep(1)
```

## 🔧 RAW Protocol (Low-level usage)

```python
from korinet import protocol

session = protocol.v2(sock)  # raw TCP socket required
session.send({"type": "ping"})

response = session.recv()
if response["status"] is not True:
    raise RuntimeError("Invalid response")
```

KoriNet exposes a **raw protocol layer** (`protocol.v2`) that can be used **directly on top of an existing TCP socket**, without the high-level `client` / `server` abstractions.

This mode is intended for **advanced users** who want:

* full control over the socket lifecycle
* minimal overhead
* a simple framed message protocol (block-based send/recv)

### ⚠️ Important limitations

When using the **RAW protocol**:

* ❌ **No automatic reconnection**
* ❌ **No session continuity**
* ❌ **No metadata for recovery**
* ❌ **No compatibility with `client` / `server`**

If the underlying **TCP socket is closed or lost**, the session is **definitively broken**.
You are fully responsible for:

* detecting disconnections
* recreating sockets
* restoring application state

This behavior is equivalent to a classic TCP protocol without resilience.

---

### 🔌 When should you use RAW protocol?

Use `protocol.v2` **only if**:

* you do **not** need reconnection
* your application tolerates socket loss
* you want a **thin, structured framing layer** on top of TCP
* you manage network failures yourself

Typical use cases:

* short-lived connections
* internal tools
* experimental protocols
* controlled environments

If you need **24/7 stability**, **automatic reconnection**, or **network fault tolerance**, use the **high-level `client` / `server` API instead**.

---

➡️ In this mode, **KoriNet only guarantees message framing**, not connection recovery.

---

### 🧠 Design note

The RAW protocol is the **foundation layer** used internally by:

* `client`
* `server`

Those high-level components add:

* reconnection logic
* session metadata
* continuity guarantees

Using `protocol.v2` bypasses all of this **by design**.