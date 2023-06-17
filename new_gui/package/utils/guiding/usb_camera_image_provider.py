import time
from package.utils.guiding.guiding_data import GuidingData
from package.utils.guiding.guiding_options import GuidingOptions
from package.utils.cameras.zwo_camera_thread import capture_from_zwo_camera
import logging
from threading import Thread, Event
import queue

log = logging.getLogger("guiding")


capture_function_map = {
    "ZWO": capture_from_zwo_camera
}


class USBCameraImageProvider:
    def __init__(self, sink, config: GuidingOptions):
        self._sink = sink
        self._vendor = config.get_camera_vendor()
        self._running = False
        self._config = config
        self._capture_thread = None
        self._process_thread = None
        self._killevent = Event()
        self._queue = queue.Queue(maxsize=2)

    def _process(self):
        index = 0
        while self._running:
            if self._queue.empty():
                time.sleep(0.1)
            else:
                imagearray = self._queue.get_nowait()
                log.debug("USB Camera: started processing queue item!")
                self._sink.put_image(GuidingData(imagearray, time.time(), f"Capture_{index}"))
                self._queue.task_done()
                log.info(f"...image put successfully")
                index += 1
        log.debug("USB Camera processing thread exiting...")

    def is_running(self):
        return self._running

    def reset_calculation(self):
        log.debug("Resetting Image Provider")
        self._sink.reset()

    def start(self):
        self._running = True
        log.debug("USBCameraImageProvider starts capture thread")
        capture_fun = capture_function_map[self._vendor]
        self._capture_thread = Thread(target=capture_fun, args=(self._config, self._queue, self._killevent,))
        self._process_thread = Thread(target=self._process)
        self._capture_thread.start()
        self._process_thread.start()

    def stop(self):
        log.debug("USBCameraImageProvider about to be stopped")
        self._running = False
        self._killevent.set()
        if self._capture_thread is not None and self._capture_thread.is_alive():
            log.debug("Waiting capture thread to be joined...")
            self._capture_thread.join()
            log.debug("joined capture thread")
        if self._process_thread is not None and self._process_thread.is_alive():
            log.debug("Waiting process thread to be joined...")
            self._process_thread.join()
            log.debug("joined process thread")
        log.debug("USB camera image provider stopped")
        self._queue.join()

