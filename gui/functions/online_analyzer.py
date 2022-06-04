from threading import Thread
import struct
from tkinter import filedialog

from .image_calculator import ImageCalculator
from .encoder_manager import just_read_encoder
from .image_provider import ImageProvider
from .speedcalculator import SpeedCalculator
from .times_generator import get_data_from_correction_file, get_new_correction_data
from .serial_handlers.all_handlers import correction_data_provider


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


def get_correction_from_mount(reader):
    if not reader.is_connected():
        return None
    reader.write_string("GET_CORR\n")
    result = correction_data_provider.get_data()
    if result is None:
        return []
    _, times, intervals = result
    data = (times, intervals)
    print(f"Obtained data from mount: {data}")
    return data


class ModelManager:
    def __init__(self, command_to_get, callback):
        self._command_to_get_correction = command_to_get
        self._callback = callback

    def handle_new_average_speed(self, speed):
        t, d = self._command_to_get_correction()
        new_data = get_new_correction_data(d, speed)
        self._callback((t, new_data))


class ByteConverter:
    def __init__(self, callback):
        self._callback = callback

    def push_new_array(self, a):
        t, i = (list(map(int, e)) for e in a)
        f = f"{len(t)}I{len(i)}I"
        print(f"Size of bytes = {struct.calcsize(f)}")
        result = struct.pack(f, *t, *i)
        self._callback((len(t), result))


class OnlineAnalyzer:
    """
    # TODO!!!
    In fully automatic online mode:
    it should be reading ***CURRENT*** images (automatically chosen dir)
    it should be reading ***CURRENT*** encoder readouts (it does)
    it should be reading ***CURRENT*** worm model by getting it from mount by serial
    """

    @staticmethod
    def _handle_speed(speed, mm, lf):
        speed_str = ", ".join(map(str, speed))
        lf.write(f"{speed_str}\n")
        mm.handle_new_average_speed(speed)

    def __init__(self, encoder_data_provider, callback, reader=None):
        self._reader = reader
        self._callback = callback
        self._average_speeds = open('average_speeds.txt', 'w')
        self._image_provider = None
        if encoder_data_provider is None:
            self._encoder_data_provider = HistoricalEncoderDataProvider()
        else:
            self._encoder_data_provider = encoder_data_provider
        self._provider_thread = None

    def kill(self):
        if self._image_provider is not None:
            self._average_speeds.close()
            self._image_provider.kill()
            self._provider_thread.join()

    def start(self):
        d = filedialog.askdirectory(title="Select directory with images:")
        # d = "C:/Users/Florek/Desktop/SharpCap Captures/LeoQuartet_cz5"
        if d is None:
            return
        print(f"Using image dir={d}")
        # f = filedialog.askopenfilename(title='Select file with correction model')
        f = "C:/Users/Florek/Desktop/workspace/PEliminator/analyzer/new_data.txt"
        if f is None:
            return
        print(f"Using correction model={f}")

        by = ByteConverter(self._callback)

        if self._reader is not None:
            def command_to_get_correction():
                return get_correction_from_mount(self._reader)
        else:
            def command_to_get_correction():
                return get_data_from_correction_file(f)

        mm = ModelManager(command_to_get_correction, by.push_new_array)
        a = SpeedCalculator(self._encoder_data_provider, lambda x: self._handle_speed(x, mm, self._average_speeds))
        c = ImageCalculator(a.add_point)
        self._image_provider = ImageProvider(d, c.new_image)
        self._provider_thread = Thread(target=self._image_provider.run)
        self._provider_thread.start()
