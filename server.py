# TODO: handle when server crashes
# TODO: thread safety
# TODO: how much to recv()
# TODO: logging instead of print()
# TODO: add functionality for client to leave
# TODO: need to get rid of thread from the dict once it's done

import dataclasses
import socket
import threading
from collections.abc import Iterable

# class Keywords(enum.StrEnum):
#     USERNAME = enum.auto()


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ClientSocket:
    # TODO: add send(), recv()
    sock: socket.socket
    ip: str
    port: int
    username: str


class Clients:
    def __init__(
        self, clients: Iterable[ClientSocket] = (), max_num_clients: int = 5
    ) -> None:
        # TODO: only add up to max
        self._max_num_clients = max_num_clients
        self._clients: dict[ClientSocket, threading.Thread] = {
            client: threading.Thread(target=self._handle_one, kwargs={"client": client})
            for client in clients
        }
        # TODO: don't start threads in __init__()
        for thread in self._clients.values():
            thread.start()

    def broadcast(self, message: bytes) -> None:
        for client in self._clients:
            client.sock.send(message)

    def add(self, client: ClientSocket) -> None:
        if self.num_clients == self._max_num_clients:
            # TODO: send message to client there's no room, close socket
            ...
        print(
            "Added client", client.username, "at IP", client.ip, "and port", client.port
        )
        client.sock.send("Connected to the server!".encode())
        self.broadcast(f"{client.username} joined the chat!".encode())
        thread = threading.Thread(target=self._handle_one, kwargs={"client": client})
        thread.start()
        self._clients[client] = thread

    def _handle_one(self, client: ClientSocket) -> None:
        while True:
            try:
                self.broadcast(client.sock.recv(1024))
            except Exception:
                client.sock.close()
                self.broadcast(
                    f"{client.username} left the chat!".encode()
                )  # FIXME: this doesn't run when expected
                break

    @property
    def num_clients(self) -> int:
        return len(self._clients)


def accept_connection(server: socket.socket) -> ClientSocket:
    client, address = server.accept()
    ip, port = address

    client.send("USERNAME".encode())
    username = client.recv(1024).decode()
    return ClientSocket(sock=client, ip=ip, port=port, username=username)


def main() -> int:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 55555))
    server.listen()

    clients = Clients()

    while True:
        client = accept_connection(server)
        clients.add(client)
        # the above needs to be in a while True. need to already have started the while True in the threadpool that
        # sees updates in self._clients and has a while True for recv() and broadcast()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
