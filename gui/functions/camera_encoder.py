from functions.recent_files_provider import RecentImagesProvider, is_file_png
from functions.global_settings import settings
from functions.simple_1d_plotter import Simple1DPlotter
from functions.image_tracking_plot import ImageTrackingPlot
from functions.camera_image_processor import CameraImageProcessor
import tkinter as tk
from tkinter import ttk


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
    def __init__(self, effector, plotter, feedback, dec_feedback, vars_dict):
        self._plotter = plotter
        self._effector = effector
        if self._effector is None:
            print("Dummy effector chosen!")
        self._processor = CameraImageProcessor(self._effector, plotter, feedback, dec_feedback, vars_dict)
        self._provider = RecentImagesProvider(self._processor, is_file_png)

    def get_amendment(self):
        return self._processor.get_scale_amendment()

    def set_amend(self, value):
        print(f"Setting new amendment: {value}")
        self._processor.amend_scale(value)

    def reset(self):
        self._plotter.clear_plot()
        self._processor.reset()

    def start(self):
        self._plotter.clear_plot()
        self._provider.start()

    def kill(self):
        self._provider.kill()


class StarDecFeedbackController:
    def __init__(self, frame):
        self._frame = frame
        self._feedback_var = tk.StringVar(value="<none>")
        self._feedback_gain_var = tk.StringVar(value=settings.get_initial_dec_feedback_gain())

        self._current_feedback_label = tk.Label(self._frame,
                                                text="DEC:", font=('calibre', 10, 'bold'))
        self._current_feedback_label.pack(side=tk.LEFT)

        self._current_feedback_display = tk.Entry(self._frame,
                                                  state="disabled", textvariable=self._feedback_var)
        self._current_feedback_display.pack(side=tk.LEFT)
        self._feedback_gain_label = tk.Label(self._frame,
                                             text="Gain:", font=('calibre', 10, 'bold'))
        self._feedback_gain_label.pack(side=tk.LEFT)

        self._feedback_gain_spin = ttk.Spinbox(self._frame, format="%.4f", increment="0.001",
                                               from_=-1, to=1, width=7, textvariable=self._feedback_gain_var)
        self._feedback_gain_spin.pack(side=tk.LEFT)

    def set_feedback(self, value):
        self._feedback_var.set(value)

    def get_feedback_gain(self):
        return float(self._feedback_gain_var.get())


class StarFeedbackController:
    def __init__(self, frame):
        self._frame = frame
        self._feedback_var = tk.StringVar(value="<none>")
        self._feedback_gain_var = tk.StringVar(value=settings.get_initial_feedback_gain())

        self._current_feedback_label = tk.Label(self._frame,
                                                text="RA feedback from stars:", font=('calibre', 10, 'bold'))
        self._current_feedback_label.pack(side=tk.LEFT)

        self._current_feedback_display = tk.Entry(self._frame,
                                                  state="disabled", textvariable=self._feedback_var)
        self._current_feedback_display.pack(side=tk.LEFT)
        self._feedback_gain_label = tk.Label(self._frame,
                                             text="Gain to feedback:", font=('calibre', 10, 'bold'))
        self._feedback_gain_label.pack(side=tk.LEFT)

        self._feedback_gain_spin = ttk.Spinbox(self._frame, format="%.4f", increment="0.001",
                                               from_=-1, to=1, width=7, textvariable=self._feedback_gain_var)
        self._feedback_gain_spin.pack(side=tk.LEFT)
        # self._enable_feedback_button = tk.Button(self._frame,
        # text="Turn on feedback from stars", command=self._enable_feedback)

    def set_feedback(self, value):
        self._feedback_var.set(value)

    def get_feedback_gain(self):
        return float(self._feedback_gain_var.get())


class SpinWithLabel:
    def __init__(self, frame, variable, name_str, **kwargs):
        self._label = tk.Label(frame, text=name_str, font=('calibre', 10, 'bold'))
        self._label.pack(side=tk.LEFT)

        self._spin = ttk.Spinbox(frame, textvariable=variable, **kwargs)
        self._spin.pack(side=tk.LEFT)


class CameraEncoderGUI:
    def __init__(self, frame, reader):
        self._image_length_var = tk.StringVar(value=settings.get_frame_length_s())
        self._kp_var = tk.StringVar(value=1.0)
        self._ki_var = tk.StringVar(value=0.2)
        self._kd_var = tk.StringVar(value=0.1)
        self._vars_dict = {"image_length": self._image_length_var,
                           "kp": self._kp_var,
                           "ki": self._ki_var,
                           "kd": self._kd_var}
        self._encoder_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        self._encoder_frame.pack(side=tk.TOP)

        self._feedback_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        self._feedback_frame.pack(side=tk.TOP)

        self._image_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        self._image_frame.pack(side=tk.TOP)

        self._image_length_indicator = SpinWithLabel(
            self._image_frame, self._image_length_var, "Image length (s):", from_=0, to=999, width=5)
        self._kp_indicator = SpinWithLabel(
            self._image_frame, self._kp_var, "Kp=", format="%.3f", increment="0.01", width=5, from_=0, to=5.0)
        self._ki_indicator = SpinWithLabel(
            self._image_frame, self._ki_var, "Ki=", format="%.3f", increment="0.01", width=5, from_=0, to=5.0)
        self._kd_indicator = SpinWithLabel(
            self._image_frame, self._kd_var, "Kd=", format="%.3f", increment="0.01", width=5, from_=0, to=5.0)

        self._feedback = StarFeedbackController(self._feedback_frame)
        self._dec_feedback = StarDecFeedbackController(self._feedback_frame)

        self._plotter = ImageTrackingPlot(frame)
        self._reader = reader
        self._camera_encoder = CameraEncoder(None, self._plotter, self._feedback,
                                             self._dec_feedback, self._vars_dict)
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
                                             self._feedback, self._dec_feedback, self._vars_dict)
        self._camera_encoder.start()
        self._button.configure(text="Stop camera encoder", command=self._stop_action)

    def _stop_action(self):
        self._camera_encoder.kill()
        self._camera_encoder = None
        self._button.configure(text="Start camera encoder", command=self._start_action)
