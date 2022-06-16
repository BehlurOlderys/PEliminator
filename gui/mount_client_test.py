from functions.mount_client import MountClient
from time import sleep


if __name__ == "__main__":
    client = MountClient()
    client.send("Hello, world!")
    sleep(3)
    client.send("End!")
