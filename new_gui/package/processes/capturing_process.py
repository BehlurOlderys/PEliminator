import multiprocessing
from package.utils.zwo_asi_camera_grabber import ASICamera
import time


def capturing(image_queue: multiprocessing.Queue, kill_event: multiprocessing.Event, **kwargs):
    ASICamera.initialize_library()

    interval_us = kwargs["interval_us"]
    camera_id = kwargs["camera_id"]
    bandwidth = kwargs["bandwidth"]
    image_type = kwargs["image_type"]
    multiplicity = kwargs["multiplicity"]
    save_file = kwargs["save_file"]

    camera = ASICamera(camera_id)
    camera.set_bandwidth(bandwidth)
    camera.set_image_type(image_type)
    camera.set_exposure_us(int(interval_us))

    last_time = time.time()

    for i in range(0, multiplicity):
        if kill_event.is_set():
            image_queue.close()
            print("Got kill command, returning!")
            exit(0)

        im = camera.capture_image()
        if save_file:
            filename = f"Capture_{i}.tif"
            pass  # TODO: save file

        if not kill_event.is_set():
            image_queue.put(im)

        # current_time = time.time()
        # total_time = current_time - last_time
        # print(f"Total time for a frame = {total_time}")
        # last_time = current_time
