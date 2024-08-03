# TODO: thread safety
# TODO: how much to recv()

import dataclasses
import socket
import threading


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ClientSocket:
    # TODO: add send(), recv()
    sock: socket.socket
    address: str
    username: str


host = "127.0.0.1"
port = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

lock = threading.Lock()

client_sockets: set[ClientSocket] = set()


def broadcast(message: bytes) -> None:
    with lock:
        for client in client_sockets:
            client.sock.send(message)


def handle(client: ClientSocket) -> None:
    try:
        while True:
            message = client.sock.recv(1024)
            broadcast(message)
    except Exception:
        with lock:
            client.sock.close()
            client_sockets.remove(client)
    finally:
        # FIXME: new client sees message about old client leaving
        broadcast(f"{client.username} left the chat!".encode())


def main() -> int:
    while True:
        client, address = server.accept()
        print(f"Connected with {address}")

        client.send("NICK".encode())
        nickname = client.recv(1024).decode()
        s = ClientSocket(sock=client, address=address, username=nickname)
        client_sockets.add(s)
        broadcast(f"{nickname} joined the chat!".encode())
        client.send("Connected to the server!".encode())

        thread = threading.Thread(target=handle, args=(s,))
        thread.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
