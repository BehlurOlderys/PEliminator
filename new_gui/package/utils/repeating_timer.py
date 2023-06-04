from threading import Timer

"""
https://stackoverflow.com/questions/24072765/timer-cannot-restart-after-it-is-being-stopped-in-python
"""


class RepeatingTimer(object):

    def __init__(self, interval_s, function, *args, **kwargs):
        self._interval_s = interval_s
        self._function = function
        self._args = args
        self._kwargs = kwargs
        self._timer = None

    def _callback(self):
        self.start()
        self._function(*self._args, **self._kwargs)

    def cancel(self):
        if self._timer is not None:
            self._timer.cancel()

    def start(self):
        self._timer = Timer(self._interval_s, self._callback)
        self._timer.start()
