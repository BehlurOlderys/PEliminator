import multiprocessing
from package.utils.zwo_asi_camera_grabber import ASICamera
import time


def capturing(interval_s, multiplicity, camera_id, image_queue: multiprocessing.Queue):
    ASICamera.initialize_library()
    interval_s = 0.04
    interval_us = 20*1000
    camera = ASICamera(camera_id)
    camera.set_bandwidth(100)
    camera.set_image_type("raw8")
    camera.set_exposure_us(int(interval_us))
    multiplicity = 10000
    refresh_rate_hz = 1.0
    min_refresh_rate_hz = 0.001 #1000s
    min_refresh_time_s = 0.2
    refresh_time_s = max(min_refresh_time_s, 1.0/max(min_refresh_rate_hz, refresh_rate_hz))
    print(f"Using refresh time = {refresh_time_s}s")
    refresh_counter_threshold = refresh_time_s//interval_s
    mark_time = time.time()
    start_time = time.time()
    average = 0
    for i in range(0, multiplicity):
        filename = f"Capture_{i}.tif"
        # print(f"Capturing image {i}/{multiplicity}, time={time.time()-start_time}")
        im = camera.capture_image()
        latest_time = time.time()
        average += (latest_time - mark_time)
        mark_time = latest_time
        if 0 == i % refresh_counter_threshold:
            print(f"Average fps = {refresh_counter_threshold/average}s")
            average = 0
            image_queue.put(im)

