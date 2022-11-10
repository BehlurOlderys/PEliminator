from package.utils.repeating_timer import RepeatingTimer
import glob
import os
from PIL import Image
import numpy as np


class ImageProvider:
    def __init__(self, queue):
        self._queue = queue


class TimedFileImageProvider(ImageProvider):
    def __init__(self, delay, directory, extension="png", *args, **kwargs):
        super(TimedFileImageProvider, self).__init__(*args, **kwargs)
        self._delay = delay
        self._directory = directory
        self._files = glob.glob(os.path.join(self._directory, f"*.{extension}"))
        print(f"Init TimedFileImageProvider with {len(self._files)} files in {self._directory}!")

        self._timer = RepeatingTimer(interval=self._delay, function=self._put_new)
        self._gen = None

    def _put_new(self):
        print("Putting new image into queue...")
        try:
            image_path = next(self._gen)
        except StopIteration:
            print("End of images, stopping Provider")
            self._timer.cancel()
            return

        im_frame = Image.open(image_path)
        np_frame = np.array(im_frame)
        self._queue.put(np_frame)

    def _provide_next_image(self):
        yield from self._files

    def start(self):
        print("Provider starts!")
        self._gen = self._provide_next_image()
        self._timer.start()

    def stop(self):
        print("Stopping image provider")
        self._timer.cancel()
