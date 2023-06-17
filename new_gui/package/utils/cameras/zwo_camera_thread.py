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
    start_time = time.time()
    is_exposure = True
    while not killme.is_set():
        now_time = time.time()
        interval_s = now_time-start_time
        state = asicam.get_camerastate()
        if is_exposure and asicam.get_imageready():
            imagebytes, _ = asicam.get_imagebytes()
            np_array = asicam.get_np_array_from_buffer(imagebytes)
            if not queue.full():
                queue.put_nowait(np_array)
            is_exposure = False
        elif is_exposure and asicam.is_image_failed():
            log.error(f"{asicam.get_name()}: Failed to capture image!")
            asicam.stopexposure()
            is_exposure = False
        elif is_exposure and asicam.is_camera_idle():
            log.warning(f"{asicam.get_name()}: Should be capturing but camera state is IDLE!")
            is_exposure = False
        elif not is_exposure and interval_s > config.get_capture_delay_s():
            exposure_s = config.get_exposure()
            log.debug(f"Starting new exposure for {exposure_s}s")
            asicam.startexposure(exposure_s)
            is_exposure = True

        time.sleep(0.1)
    asicam.stopexposure()
