from threading import Thread
import numpy as np

IMAGE_QUEUE_TIMEOUT_S = 5


class ImageConsumer:
    def __init__(self, queue, display_callback, calculate_callback):
        self._image_queue = queue
        self._thread = None
        self._kill = False
        self._display_callback = display_callback
        self._calculate_callback = calculate_callback

    def start(self):
        self._kill = False
        self._thread = Thread(target=self._run)
        self._thread.start()

    def stop(self):
        self._kill = True
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()

    def _run(self):
        while not self._kill:
            print("Waiting for new image...")
            image, time = self._image_queue.get(timeout=IMAGE_QUEUE_TIMEOUT_S)
            if image is None:
                print("Returning from handle images thread")
                return
            if self._kill:
                return

            self._calculate_callback((image, time))
            self._display_callback(image)
