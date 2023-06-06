from .zwo_camera import ZwoCamera
from package.utils.guiding.guiding_options import GuidingOptions
import time
import logging
from threading import Event
from queue import Queue
log = logging.getLogger("guiding")


def capture_from_zwo_camera(config: GuidingOptions, queue: Queue, killme: Event):
    log.debug("ZWO Camera capture thread init...")
    cameras = ZwoCamera.get_cameras_list()
    index = cameras.index(config.get_camera_name())
    asicam = ZwoCamera(index)
    asicam.set_gain(config.get_gain())
    asicam.set_readoutmode_str(config.get_image_type())
    log.debug("Starting new exposure...")
    asicam.startexposure(config.get_exposure())
    while not killme.is_set():
        if asicam.get_imageready():
            imagebytes, _ = asicam.get_imagebytes()
            log.debug("Starting new exposure...")
            np_array = asicam.get_np_array_from_buffer(imagebytes)
            if not queue.full():
                queue.put_nowait(np_array)
            asicam.startexposure(config.get_exposure())
        time.sleep(0.1)

    asicam.stopexposure()
