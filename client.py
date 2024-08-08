import socket
import threading

username = input("Choose a username: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 55555))


def receive() -> None:
    while True:
        try:
            message = client.recv(1024).decode("ascii")
            if message == "USERNAME":
                client.send(username.encode("ascii"))
            else:
                print(message)
        except Exception:
            print("An error occured!")
            client.close()
            break


def write() -> None:
    while True:
        message = f'{username}: {input("Enter a message:")}'
        client.send(message.encode("ascii"))


receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
