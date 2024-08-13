# TODO: handle when server crashes
# TODO: thread safety/locks
# TODO: how much to recv()
# TODO: add functionality for client to leave
# TODO: keep track of futures?

import concurrent.futures
import dataclasses
import logging
import socket


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

    def recv(self, n: int = 2**10) -> str:
        return self.sock.recv(n).decode()


class Clients:
    def __init__(self, max_num_clients: int = 5) -> None:
        self._max_num_clients = max_num_clients
        self._clients: set[ClientSocket] = set()
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_num_clients
        )

    def _start_handling_one_client(self, client: ClientSocket) -> None:
        self._clients.add(client)
        future = self._thread_pool.submit(self._handle_one, client=client)
        future.add_done_callback(lambda f: self._clients.remove(f.result()))

    def broadcast(self, message: str) -> None:
        for client in self._clients:
            client.send(message)

    def add(self, client: ClientSocket) -> None:
        if self.num_clients == self._max_num_clients:
            self._reject_client_since_full(client)
            return None

        logger.info(
            "Added client %s at IP %s and port %d.",
            client.username,
            client.ip,
            client.port,
        )
        client.send("Connected to the server!")
        self.broadcast(f"{client.username} joined the chat!")
        self._start_handling_one_client(client)

    def _reject_client_since_full(self, client: ClientSocket) -> None:
        logger.warning("Room is full, unable to add new client.")
        client.send("Room is full, try again later.")
        client.close()

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

    def bind(self, ip: str, port: int) -> None:
        self._socket.bind((ip, port))

    def listen(self) -> None:
        self._socket.listen()

    def accept_connection(self) -> None:
        client, address = self._socket.accept()
        self._add_client(client, *address)

    def _add_client(self, client: socket.socket, ip: str, port: int) -> None:
        client.send("USERNAME".encode())
        username = client.recv(2**10).decode()
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
