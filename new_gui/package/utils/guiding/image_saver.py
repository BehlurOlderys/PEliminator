from .data_processor import DataProcessor
from .guiding_data import GuidingData
from PIL import Image
import os
import logging
log = logging.getLogger("guiding")


class ImageSaver(DataProcessor):
    def __init__(self, prefix, save_path):
        super(ImageSaver, self).__init__("ImageSaver")
        self._prefix = prefix
        self._save_path = save_path
        if not os.path.isdir(self._save_path):
            try:
                os.mkdir(self._save_path)
            except Exception as e:
                log.error(f"Could not create directory {self._save_path}: {repr(e)}")

    def _process_impl(self, data: GuidingData):
        im = Image.fromarray((256*data.image).astype('uint8'))
        no_ext = data.shortname.split(".")[0]
        image_new_path = os.path.join(self._save_path, self._prefix + "_" + no_ext + ".jpg")

        try:
            im.save(image_new_path)
        except Exception as e:
            log.error(f"Could not save file {image_new_path}: {repr(e)}")
            return None
        log.info(f"Saved image as {image_new_path}")
        return data
