from tkinter import filedialog
from .image_calculator import ImageCalculator
from .encoder_manager import just_read_encoder
from .image_provider import ImageProvider
from .corrector import Corrector
from threading import Thread


class HistoricalEncoderDataProvider:
    def __init__(self):
        self._data = None

    def _read_file(self):
        # f = filedialog.askopenfilename(title='Select file with encoder data')
        f = "C:/Users/Florek/Desktop/workspace/PEliminator/gui/logs/encoder_log_2022-03-25_00-01"
        if f is not None:
            print(f"Loading encoder log {f}...")
            self._data = just_read_encoder(f)
            self._data = {k: v[1] for k, v in self._data.items()}
            print("Loading encoder log finished!")
            print(list(self._data)[:10])

    def find_readout_by_timestamp(self, t):
        if self._data is None:
            self._read_file()

        timestamp = int(t)
        if timestamp not in self._data:
            return None
        return self._data[timestamp]


class OnlineAnalyzer:
    """
    # TODO!!!
    In fully automatic online mode:
    it should be reading ***CURRENT*** images (automatically chosen dir)
    it should be reading ***CURRENT*** encoder readouts (it does)
    it should be reading ***CURRENT*** worm model by getting it from mount by serial
    """
    def __init__(self, encoder_data_provider):
        self._image_provider = None
        if encoder_data_provider is None:
            self._encoder_data_provider = HistoricalEncoderDataProvider()
        else:
            self._encoder_data_provider = encoder_data_provider

    def kill(self):
        if self._image_provider is not None:
            self._image_provider.kill()

    def start(self):
        # d = filedialog.askdirectory(title="Select directory with images:")
        d = "C:/Users/Florek/Desktop/SharpCap Captures/LeoQuartet_cz5"
        if d is None:
            return
        print(f"Using image dir={d}")
        # f = filedialog.askopenfilename(title='Select file with correction model')
        f = "C:/Users/Florek/Desktop/workspace/PEliminator/analyzer/new_data.txt"
        if f is None:
            return
        print(f"Using correction model={f}")
        a = Corrector(self._encoder_data_provider, lambda x: print(x), f)
        c = ImageCalculator(a.add_point)
        self._image_provider = ImageProvider(d, c.new_image)
        onliner_thread = Thread(target=self._image_provider.run)
        onliner_thread.start()
