from package.utils.guiding.guiding_options import GuidingOptions
from package.utils.guiding.guiding_data import GuidingData
from package.utils.repeating_timer import RepeatingTimer
import glob
import os
import time
import numpy as np
import logging

from PIL import Image
from astropy.io import fits

log = logging.getLogger("guiding")


def get_np_array_from_fits(filepath):
    hdul = fits.open(filepath)
    image_data = hdul[0].data
    return image_data


def get_np_array_from_png(filepath):
    im_frame = Image.open(filepath)
    return np.array(im_frame)


image_openers_map = {
    "fits": get_np_array_from_fits,
    "png": get_np_array_from_png
}


class DirectoryTimedImageProvider:
    def __init__(self, sink, config: GuidingOptions):
        path = config.get_sim_path()
        extension = config.get_sim_extension()
        delay_s = int(config.get_sim_delay_s())
        self._files = glob.glob(os.path.join(path, f"*.{extension}"))
        self._delay_s = delay_s
        self._directory = path
        self._sink = sink
        self._image_opener = image_openers_map.get(extension, None)
        self._files = glob.glob(os.path.join(self._directory, f"*.{extension}"))
        log.info(f"Init TimedFileImageProvider with {len(self._files)} files in {self._directory}!")
        self._timer = RepeatingTimer(interval_s=self._delay_s, function=self._put_new)
        self._gen = None
        self._busy = False
        self._running = False

    def _put_new(self):
        self._busy = True
        log.debug("Trying to put new image...")
        try:
            image_path = next(self._gen)
        except StopIteration:
            log.info("End of images, stopping Provider")
            self._timer.cancel()
            return

        try:
            np_image = self._image_opener(image_path)

        except Exception as e:
            log.warning(f"Opening file {image_path} failed: {repr(e)}")
            return
        short_name = image_path.split('\\')[-1]

        self._sink.put_image(GuidingData(np_image, time.time(), short_name))
        self._busy = False
        log.info(f"...image {short_name} put successfully")

    def _provide_next_image(self):
        yield from self._files

    def is_running(self):
        return self._running

    def start(self):
        log.debug("DirectoryTimedImageProvider starts")
        self._running = True
        self._gen = self._provide_next_image()
        self._timer.start()

    def stop(self):
        self._timer.cancel()
        for i in range(0, 10):
            if self._busy:
                time.sleep(0.2)
            else:
                break
        self._running = False
        log.debug("DirectoryTimedImageProvider stopped")
