import os

from gui.functions.image_provider import ImageProvider
from gui.functions.image_calculator import ImageCalculator
from threading import Thread


if __name__ == "__main__":
    d = os.path.join(os.getcwd(), "trash")
    c = ImageCalculator(lambda x: print(f"Calculated new center: {x}"))
    i = ImageProvider(d, c.new_image)
    t = Thread(target=i.run)
    t.start()
    t.join()
