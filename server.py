# TODO: handle when server crashes
# TODO: thread safety/locks
# TODO: how much to recv()
# TODO: add functionality for client to leave
# TODO: keep track of futures?

import concurrent.futures
import dataclasses
import logging
import os
import socket
from collections.abc import Iterable


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# class Keywords(enum.StrEnum):
#     USERNAME = enum.auto()


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ClientSocket:
    sock: socket.socket
    ip: str
    port: int
    username: str

    def close(self) -> None:
        self.sock.close()

    def send(self, s: str, /) -> None:
        self.sock.send(s.encode())

    def recv(self, n: int = 1024) -> str:
        return self.sock.recv(n).decode()


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

    def broadcast(self, message: str) -> None:
        for client in self._clients:
            client.send(message)

    def add(self, client: ClientSocket) -> None:
        if self.num_clients == self._max_num_clients:
            logger.warning("Room is full, unable to add new client.")
            client.send("Room is full, try again later.")
            client.close()
            return None

        logger.info(
            "Added client %s at IP %s and port %d.",
            client.username,
            client.ip,
            client.port,
        )
        client.send("Connected to the server!")
        self.broadcast(f"{client.username} joined the chat!")
        self._clients.add(client)
        future = self._thread_pool.submit(self._handle_one, client=client)
        future.add_done_callback(lambda f: self._clients.remove(f.result()))

    def _handle_one(self, client: ClientSocket) -> ClientSocket:
        while True:
            try:
                self.broadcast(client.recv())
            except Exception:
                client.close()
                self.broadcast(
                    f"{client.username} left the chat!"
                )  # FIXME: this doesn't run when expected
                return client

    @property
    def num_clients(self) -> int:
        return len(self._clients)


class Server:
    def __init__(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._clients = Clients()

    def bind(self, ip: str | None, port: int | None) -> None:
        if ip is None:
            ip = os.environ["IP"]
        if port is None:
            port = int(os.environ["PORT"])
        self._socket.bind((ip, port))

    def listen(self) -> None:
        self._socket.listen()

    def accept_connection(self) -> None:
        client, address = self._socket.accept()
        ip, port = address

        client.send("USERNAME".encode())
        username = client.recv(1024).decode()
        self._clients.add(
            ClientSocket(sock=client, ip=ip, port=port, username=username)
        )


def main() -> int:
    server = Server()
    server.bind(ip="127.0.0.1", port=55555)
    server.listen()

    while True:
        server.accept_connection()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
