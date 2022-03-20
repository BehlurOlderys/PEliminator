import os

from widgets.image_provider import ImageProvider
from threading import Thread


if __name__ == "__main__":
    d = os.path.join(os.getcwd(), "trash")
    i = ImageProvider(d, lambda x: print(f"Acquired new file: {x}"))
    t = Thread(target=i.run)
    t.start()
    t.join()
