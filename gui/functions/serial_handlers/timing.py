import time
from datetime import datetime
from struct import unpack

from .averager import averager
from .common import timing_log_index

last_timestamp = None
last_micros = 0
last_millis = 0
last_real = 0
average_ratio = None
average_size = 0
last_datetime = None


def deserialize_timing(raw_payload, timestamp, logs):
    # BELOW IS FOR CONTROLLING TRACKING INTERVAL:
    # global last_millis, last_real, last_micros
    # [raw_millis, real_millis] = [int(x) for x in unpack("II", raw_payload)]
    # interval = raw_millis - last_millis
    # interval_real = real_millis - last_real
    # pc_micros = round(time.time_ns() / 1000)
    # pc_interval = pc_micros - last_micros
    # difference = 399720 - pc_interval
    # mean_diff = 0
    # if last_millis > 0:
    #     a, _ = averager.update_average(difference)
    #     mean_diff = a
    # print(f"Raw = {raw_millis},"
    #       f" adjusted = {real_millis}, "
    #       f"interval = {interval}, "
    #       f"real interval = {interval_real},"
    #       f"pc_interval = {pc_interval},"
    #       f"mean_diff = {mean_diff}")
    # last_millis = raw_millis
    # last_real = real_millis
    # last_micros = pc_micros

    # BELOW VERSION FOR CONTROLLING TIME DRIFT:
    global last_timestamp, last_micros, last_datetime
    [prev_micros, current_millis] = [int(x) for x in unpack("II", raw_payload)]
    logger = logs[timing_log_index]
    pc_micros = round(time.time_ns() / 1000)
    logger.write(f"{timestamp}, {prev_micros}, {current_millis}, {pc_micros}\n")
    loop_constant = (timestamp - prev_micros) / 5000
    dt = datetime.now()
    if last_timestamp is not None:
        interval_on_arduino = timestamp - last_timestamp
        interval_pc_micros = pc_micros - last_micros
        ratio = interval_pc_micros / interval_on_arduino
        mean_ratio, ratios_size = averager.update_average(ratio)
        delta_dt = (dt - last_datetime)
        print(f"Arduino interval = {interval_on_arduino},"
              f" PC interval = {interval_pc_micros},"
              f" delta_dt = {delta_dt},"
              f" loop = {loop_constant},"
              f" ratio = {ratio},"
              f" mean ratio = {mean_ratio}, size={ratios_size}")

    last_timestamp = timestamp
    last_micros = pc_micros
    last_datetime = dt