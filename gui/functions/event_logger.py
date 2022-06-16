from threading import Event
import tkinter as tk


class EventLogger:
    def __init__(self):
        self._log_some_string = Event()
        self._log_strings = []
        self._killer_flag = False

    def kill(self):
        self._killer_flag = True

    def log_event(self, s):
        print(s)

    def run(self, scrolled_text):
        while not self._killer_flag:
            result = self._log_some_string.wait(1)
            if result:
                self._log_some_string.clear()
            else:
                continue
            scrolled_text.configure(state='normal')
            while self._log_strings:
                scrolled_text.insert(tk.INSERT, self._log_strings.pop(0))
                scrolled_text.configure(state='disabled')
