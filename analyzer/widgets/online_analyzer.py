from tkinter import filedialog
from .image_calculator import ImageCalculator
from .image_provider import ImageProvider
from .corrector import Corrector
from threading import Thread


class OnlineAnalyzer:
    def __init__(self, encoder_data_provider):
        self._image_provider = None
        self._encoder_data_provider = encoder_data_provider

    def kill(self):
        if self._image_provider is not None:
            self._image_provider.kill()

    def start(self):
        d = filedialog.askdirectory(title="Select directory with images:")
        a = Corrector(self._encoder_data_provider)
        c = ImageCalculator(a.add_point)
        self._image_provider = ImageProvider(d, c.new_image)
        onliner_thread = Thread(target=self._image_provider.run)
        onliner_thread.start()