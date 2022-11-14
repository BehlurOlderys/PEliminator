import numpy as np


class ErrorHandler:
    def __init__(self, write_queue, read_queue, scale_getter, angle_getter):
        self._rq = read_queue
        self._wq = write_queue
        self._pause = True
        self._scale_getter = scale_getter
        self._angle_getter = angle_getter

    def start(self):
        self._pause = False

    def stop(self):
        self._pause = True

    def handle_error(self, ex, ey):
        ra_scale, dec_scale = self._scale_getter()
        angle = self._angle_getter()
        """
        It is assumed that 0deg is direction 
        where stars are running towards right edge
        when mount is not moving.
        """
        E = np.array((ex, ey)).transpose()
        theta = np.radians(angle)
        c, s = np.cos(theta), np.sin(theta)
        R = np.array(((c, -s), (s, c)))

        corr = np.divide(R.dot(E), np.array((ra_scale, dec_scale)))

        steps_ra = int(corr[0])
        steps_dec = int(corr[1])
        print(f"Steps RA= {steps_ra}, steps DEC= {steps_dec}")
