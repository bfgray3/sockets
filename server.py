# TODO: handle when server crashes
# TODO: thread safety/locks
# TODO: how much to recv()
# TODO: logging instead of print()
# TODO: add functionality for client to leave
# TODO: keep track of futures?

import concurrent.futures
import dataclasses
import socket
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
        self._max_num_clients = max_num_clients
        self._clients = set()
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_num_clients
        )
        # TODO: don't start threads in __init__()
        for i, client in enumerate(clients, start=1):
            if i == self._max_num_clients:
                break  # TODO: warn ignoring the rest
            # TODO: next three lines should be made into a function and reused in add()
            self._clients.add(client)
            future = self._thread_pool.submit(self._handle_one, client=client)
            future.add_done_callback(lambda f: self._clients.remove(f.result()))

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
        self._clients.add(client)
        future = self._thread_pool.submit(self._handle_one, client=client)
        future.add_done_callback(lambda f: self._clients.remove(f.result()))

    def _handle_one(self, client: ClientSocket) -> ClientSocket:
        while True:
            try:
                self.broadcast(client.sock.recv(1024))
            except Exception:
                client.sock.close()
                self.broadcast(
                    f"{client.username} left the chat!".encode()
                )  # FIXME: this doesn't run when expected
                return client

    @property
    def num_clients(self) -> int:
        return len(self._clients)


# TODO: make Server class
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
        clients.add(accept_connection(server))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
