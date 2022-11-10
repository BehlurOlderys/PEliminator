from threading import Thread
import numpy as np

IMAGE_QUEUE_TIMEOUT_S = 5


class ImageConsumer:
    def __init__(self, queue, callback):
        self._image_queue = queue
        self._thread = None
        self._kill = False
        self._callback = callback

    def start(self):
        self._kill = False
        self._thread = Thread(target=self._run)
        self._thread.start()

    def stop(self):
        self._kill = True
        self._thread.join()

    def _run(self):
        while not self._kill:
            print("Waiting for new image...")
            image = self._image_queue.get(timeout=IMAGE_QUEUE_TIMEOUT_S)
            if image is None:
                print("Returning from handle images thread")
                return
            if self._kill:
                return
            c = 255 / np.log(1 + np.max(image))
            log_image = c * (np.log(image + 1))
            log_image = np.array(log_image, dtype=np.uint8)

            self._callback(log_image)
