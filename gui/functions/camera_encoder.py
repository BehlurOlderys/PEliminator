from functions.zwo_asi_camera_grabber import ASICamera
from functions.global_settings import settings
from functions.image_tracking_plot import ImageTrackingPlot
from functions.camera_image_processor import CameraImageProcessor
from functions.spin_with_label import SpinWithLabel
from functions.dithering_controller import DitheringControllerGUI
from functions.pid_controller import PIDGUI
import tkinter as tk
import time
from tkinter import ttk
from threading import Thread, Event

waiting_event = Event()


dummy_effector_label = "Dummy output"
serial_effector_label = "Serial output"
available_effectors = [serial_effector_label, dummy_effector_label]


class SerialEffector:
    def __init__(self, serial):
        self._serial = serial

    def effect(self, command):
        self._serial.write_immediately(command.encode())


class DummyEffector:
    def effect(self, command):
        print(command)


class CameraEncoder:
    def __init__(self, effector, plotter, ra_feedback, dec_feedback, dithering_ra, vars_dict):
        self._plotter = plotter
        self._effector = effector
        if self._effector is None:
            print("Dummy effector chosen!")
        self._dithering_ra = dithering_ra
        self._processor = CameraImageProcessor(self._effector, plotter, ra_feedback, dec_feedback, vars_dict)
        self._camera = ASICamera()
        self._killme = False
        self._thread = None

    def get_amendment(self):
        return self._processor.get_scale_amendment()

    def send_dither_as(self, value_as):
        self._processor.add_ra_set_point_as(value_as)

    def set_amend(self, value):
        print(f"Setting new amendment: {value}")
        self._processor.amend_scale(value)

    def reset(self):
        self._plotter.clear_plot()
        self._processor.reset()

    def _run(self):
        while not self._killme:
            waiting_event.wait(2)
            image_buffer = self._camera.capture_image()
            self._dithering_ra.step()
            self._processor.process(image_buffer, time.time())

    def start(self):
        self._plotter.clear_plot()
        self._camera.connect_and_prepare_camera(roi=(400, 512))
        image_buffer = self._camera.capture_image()
        self._processor.init(image_buffer, time.time())
        self._thread = Thread(target=self._run)
        self._thread.start()

    def kill(self):
        self._killme = True
        if self._thread is not None and self._thread.ident is not None:
            self._thread.join()


class FeedbackController:
    def __init__(self, frame, feedback_title):
        self._frame = frame
        self._feedback_var = tk.StringVar(value=0)
        self._current_feedback_label = tk.Label(self._frame,
                                                text=feedback_title, font=('calibre', 10, 'bold'))
        self._current_feedback_label.pack(side=tk.LEFT)

        self._current_feedback_display = tk.Entry(self._frame,
                                                  state="disabled", textvariable=self._feedback_var)
        self._current_feedback_display.pack(side=tk.LEFT)

    def set_feedback(self, value):
        self._feedback_var.set(value)


class CameraEncoderGUI:
    def __init__(self, frame, reader):
        self._image_length_var = tk.StringVar(value=settings.get_frame_length_s())

        self._vars_dict = {"image_length": self._image_length_var}

        self._encoder_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        self._encoder_frame.pack(side=tk.TOP)

        self._feedback_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        self._feedback_frame.pack(side=tk.TOP)

        self._image_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        self._image_frame.pack(side=tk.TOP)

        self._main_pid_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        self._main_pid_frame.pack(side=tk.TOP, anchor=tk.E)
        self._main_pid = PIDGUI(self._main_pid_frame, "main_pid", self._vars_dict,
                                label="Main RA PID settings:")

        self._long_ra_pid_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        self._long_ra_pid_frame.pack(side=tk.TOP, anchor=tk.E)
        self._long_ra_pid = PIDGUI(self._long_ra_pid_frame, "long_ra_pid", self._vars_dict,
                                   label="Long term RA PID settings:")

        self._long_dec_pid_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        self._long_dec_pid_frame.pack(side=tk.TOP, anchor=tk.E)
        self._long_dec_pid = PIDGUI(self._long_dec_pid_frame, "long_dec_pid", self._vars_dict,
                                    label="Long term DEC PID settings:")

        self._image_length_indicator = SpinWithLabel(
            self._image_frame, self._image_length_var, "Image length (s):", from_=0, to=999, width=5)

        self._dithering_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        self._dithering_frame.pack(side=tk.TOP, anchor=tk.W)
        self._ra_dithering = DitheringControllerGUI(
            self._dithering_frame, "RA dithering", lambda x: self._camera_encoder.send_dither_as(x))

        self._ra_feedback = FeedbackController(self._feedback_frame, "Current RA error:")
        self._dec_feedback = FeedbackController(self._feedback_frame, "Current DEC error:")

        self._plotter = ImageTrackingPlot(frame)
        self._reader = reader
        self._camera_encoder = CameraEncoder(None, self._plotter, self._ra_feedback,
                                             self._dec_feedback, self._ra_dithering, self._vars_dict)
        self._choice = tk.StringVar(value=available_effectors[0])
        self._reset_button = tk.Button(self._encoder_frame, text="Reset camera encoder",
                                       command=self._camera_encoder.reset)
        self._reset_button.pack(side=tk.RIGHT)
        self._amendment = tk.StringVar(value=int(100*self._camera_encoder.get_amendment()))
        self._amendment_spin = ttk.Spinbox(self._encoder_frame, from_=-999, to=999,
                                           width=5, textvariable=self._amendment)
        self._amendment_spin.pack(side=tk.RIGHT)
        self._amend_button = tk.Button(self._encoder_frame, text="Set encoder amendment",
                                       command=lambda: self._camera_encoder.set_amend
                                       (int(self._amendment_spin.get()) / 100)
                                       )
        self._amend_button.pack(side=tk.RIGHT)

        self._button = tk.Button(self._encoder_frame,
                                 text="Start camera encoder", command=self._start_action)
        self._button.pack(side=tk.LEFT)

        self._combobox = ttk.Combobox(self._encoder_frame, textvariable=self._choice,
                                      values=available_effectors)
        self._combobox.pack(side=tk.RIGHT)

    def kill(self):
        self._camera_encoder.kill()

    def _start_action(self):
        effector = None
        choice = self._choice.get()
        if choice == serial_effector_label:
            effector = SerialEffector(self._reader)
        else:
            effector = DummyEffector()

        self._camera_encoder = CameraEncoder(effector, self._plotter,
                                             self._ra_feedback, self._dec_feedback, self._vars_dict)
        self._camera_encoder.start()
        self._button.configure(text="Stop camera encoder", command=self._stop_action)

    def _stop_action(self):
        self._camera_encoder.kill()
        self._camera_encoder = None
        self._button.configure(text="Start camera encoder", command=self._start_action)
