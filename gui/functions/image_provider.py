import os
import time
from functions.utils import is_acceptable_file


class ImageProvider:
    def __init__(self, directory, callback):
        self._dir = directory
        self._files = []
        self._callback = callback
        self._killme = False

    def kill(self):
        self._killme = True

    def run(self):
        while self._killme is False:
            files = [os.path.join(self._dir, f) for f in os.listdir(self._dir) if is_acceptable_file(f)]
            new_files = [f for f in files if f not in self._files]
            for f in new_files:
                self._files.append(f)
                self._callback(f)

            time.sleep(1)
