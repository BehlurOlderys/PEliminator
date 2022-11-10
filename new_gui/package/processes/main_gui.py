from package.widgets.application import SimpleGuiApplication
from .guiding_process import GuidingProcessGUI
from .survey_process import SurveyProcessGUI
from multiprocessing import Process, Event
from tkinter import ttk
import tkinter as tk


guiding_process_key = "guiding"
survey_process_key = "survey"

child_alive_check_timeout_ms = 1000


def guiding(serial_out_queue, serial_in_queue, ke):
    gui = GuidingProcessGUI(serial_out_queue=serial_out_queue, serial_in_queue=serial_in_queue, kill_event=ke)
    gui.run()


def survey(serial_out_queue, serial_in_queue, ke):
    gui = SurveyProcessGUI(serial_out_queue=serial_out_queue, serial_in_queue=serial_in_queue, kill_event=ke)
    gui.run()


class MainGui(SimpleGuiApplication):
    def __init__(self, serial_out_queue, serial_in_queue, *args, **kwargs):
        super(MainGui, self).__init__(title="MainGUI", *args, **kwargs)
        self._serial_out = serial_out_queue
        self._serial_in = serial_in_queue
        self._root.protocol('WM_DELETE_WINDOW', self._kill_me_and_children)

        guiding_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        guiding_frame.pack(side=tk.TOP)

        self._guiding_button = ttk.Button(guiding_frame, text="Open guiding...",
                                          command=self._open_guiding, style="B.TButton")
        self._guiding_button.pack(side=tk.LEFT)

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        survey_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        survey_frame.pack(side=tk.TOP)

        self._survey_button = ttk.Button(survey_frame, text="Open survey mode...",
                                         command=self._open_survey, style="B.TButton")
        self._survey_button.pack(side=tk.LEFT)

        self._start_process_buttons = {
            guiding_process_key: self._guiding_button,
            survey_process_key: self._survey_button
        }

        self._processes = {}

    def run(self):
        self._root.after(child_alive_check_timeout_ms, self._check_if_children_alive)
        super(MainGui, self).run()

    def _kill_me_and_children(self):
        self._root.destroy()
        for k, (p, e) in self._processes.items():
            print(f"Killing process {k}")
            e.set()

        self._serial_out.put('KILL_ME_PLEASE')

    def _check_if_children_alive(self):
        for k in list(self._processes.keys()):
            p, e = self._processes[k]
            if e.is_set() or not p.is_alive():
                p.join()
                print(f"Process >> {k} << is dead and joined!")
                del self._processes[k]
                self._start_process_buttons[k].configure(state=tk.NORMAL)

        self._root.after(child_alive_check_timeout_ms, self._check_if_children_alive)

    def _open_guiding(self):
        print("Opening guiding...")
        if guiding_process_key not in self._processes.keys():
            e = Event()
            p = Process(target=guiding, args=(self._serial_out, self._serial_in, e, ))
            p.start()
            self._processes[guiding_process_key] = (p, e)
            self._guiding_button.configure(state=tk.DISABLED)

    def _open_survey(self):
        print("Opening survey...")
        if survey_process_key not in self._processes.keys():
            e = Event()
            p = Process(target=survey, args=(self._serial_out, self._serial_in, e,))
            p.start()
            self._processes[survey_process_key] = (p, e)
            self._survey_button.configure(state=tk.DISABLED)
