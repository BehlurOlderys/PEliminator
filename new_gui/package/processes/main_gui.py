from package.widgets.application import SimpleGuiApplication
from .guiding_process import GuidingProcessGUI
from .survey_process import SurveyProcessGUI
from .acquisition_process import AcquisitionProcessGUI
from .remote_process import RemoteProcessGUI
from multiprocessing import Process, Event
from tkinter import ttk
import tkinter as tk


guiding_process_key = "guiding"
survey_process_key = "survey"
acq_process_key = "acquisition"
remote_process_key = "remote"

child_alive_check_timeout_s = 1


def guiding(ke, serial_out_queue, serial_in_queue):
    gui = GuidingProcessGUI(serial_out_queue=serial_out_queue, serial_in_queue=serial_in_queue, kill_event=ke)
    gui.run()


def remote(ke):
    gui = RemoteProcessGUI(kill_event=ke)
    gui.run()


def survey(ke, serial_out_queue, serial_in_queue):
    gui = SurveyProcessGUI(serial_out_queue=serial_out_queue, serial_in_queue=serial_in_queue, kill_event=ke)
    gui.run()


def acquisition(ke):
    gui = AcquisitionProcessGUI(kill_event=ke)
    gui.run()


class MainGui(SimpleGuiApplication):
    def __init__(self, serial_out_queue, serial_in_queue, *args, **kwargs):
        super(MainGui, self).__init__(title="MainGUI", *args, **kwargs)
        self._serial_out = serial_out_queue
        self._serial_in = serial_in_queue
        self._root.protocol('WM_DELETE_WINDOW', self._kill_me_and_children)
        super(MainGui, self)._add_task(timeout_s=child_alive_check_timeout_s,
                                       f=self._check_if_children_alive)

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

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        acquisition_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        acquisition_frame.pack(side=tk.TOP)

        self._acq_button = ttk.Button(acquisition_frame, text="Open acquisition...",
                                         command=self._open_acq, style="B.TButton")
        self._acq_button.pack(side=tk.LEFT)

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        remote_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        remote_frame.pack(side=tk.TOP)
        self._remote_button = ttk.Button(remote_frame, text="Open remote camera...",
                                         command=self._open_remote, style="B.TButton")
        self._remote_button.pack(side=tk.LEFT)

        self._start_process_buttons = {
            guiding_process_key: self._guiding_button,
            survey_process_key: self._survey_button,
            acq_process_key: self._acq_button,
            remote_process_key: self._remote_button
        }

        self._processes = {}

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

    def _open_process(self, button, func, key, args: list = []):
        print(f"Opening {key}...")
        if key not in self._processes.keys():
            e = Event()
            p = Process(target=func, args=(e, *args,))
            p.start()
            self._processes[key] = (p, e)
            button.configure(state=tk.DISABLED)

    def _open_guiding(self):
        self._open_process(button=self._guiding_button, func=guiding, key=guiding_process_key,
                           args=(self._serial_out, self._serial_in))

    def _open_acq(self):
        self._open_process(button=self._acq_button, func=acquisition, key=acq_process_key)

    def _open_survey(self):
        self._open_process(button=self._survey_button, func=survey, key=survey_process_key,
                           args=(self._serial_out, self._serial_in))

    def _open_remote(self):
        self._open_process(button=self._remote_button, func=remote, key=remote_process_key)
