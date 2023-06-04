from package.widgets.labeled_combo import LabeledCombo
from package.widgets.labeled_input import LabeledInput
from package.widgets.dir_chooser import DirChooser
import tkinter as tk
import logging
log = logging.getLogger("guiding")


guiding_type_prevalue = "Simulation"
usb_camera_serial_prevalue = "COM1"
simulation_file_type_prevalue = "fits"
simulation_delay_s_prevalue = 2
camera_exposure_s_prevalue = 1
camera_gain_prevalue = 100

initial_test_dir = "C:\\Users\\Florek\\Desktop\\SharpCap Captures\\test_files"


class GuidingOptions:
    def __init__(self, frame):
        self._frame = frame
        self._guiding_combo = LabeledCombo("Guiding type",
                                     ["Simulation", "USB Camera"],
                                     prevalue=guiding_type_prevalue,
                                     event_handler=self._modified,
                                     frame=self._frame).pack(side=tk.TOP)
        self._current = guiding_type_prevalue
        self._additional_widgets = {}
        self._choose_setup()

    def get_sim_path(self):
        return self._additional_widgets["path_chooser"].get_value()

    def get_sim_extension(self):
        return self._additional_widgets["file_type"].get_value()

    def get_sim_delay_s(self):
        return self._additional_widgets["delay_input"].get_value()

    def get_guiding_type(self):
        return self._guiding_combo.get_value()

    def _choose_setup(self):
        if self._current == "Simulation":
            self._setup_for_simulation()
        elif self._current == "USB Camera":
            self._setup_for_usb_camera()
        else:
            log.warning(f"Value not handled: {self._current}")

    def _setup_for_any_camera(self):
        exposure = LabeledInput("Exposure [s]:", initial_value=camera_exposure_s_prevalue, frame=self._frame).pack(side=tk.TOP)
        gain = LabeledInput("Gain:", initial_value=camera_gain_prevalue, frame=self._frame).pack(side=tk.TOP)

        self._additional_widgets["exposure"] = exposure
        self._additional_widgets["gain"] = gain

    def _setup_for_usb_camera(self):
        usb_combo = LabeledCombo("Choose serial port",
                                 ["COM1", "COM2", "COM3"],
                                 prevalue=usb_camera_serial_prevalue,
                                 frame=self._frame).pack(side=tk.TOP)
        self._additional_widgets["usb_combo"] = usb_combo
        self._setup_for_any_camera()

    def _setup_for_simulation(self):
        delay_input = LabeledInput("Delay [s]:", initial_value=simulation_delay_s_prevalue, frame=self._frame).pack(side=tk.TOP)
        file_type_combo = LabeledCombo("Input file type",
                                             ["fits", "png", "tiff"],
                                             prevalue=simulation_file_type_prevalue,
                                             frame=self._frame).pack(side=tk.TOP)
        path_chooser = DirChooser(frame=self._frame,
                                  initial_dir=initial_test_dir).pack(side=tk.TOP)
        self._additional_widgets["file_type"] = file_type_combo
        self._additional_widgets["path_chooser"] = path_chooser
        self._additional_widgets["delay_input"] = delay_input

    def _modified(self, event):
        new_value = event.widget.get()
        log.debug(f"Value selected on guiding type combo: {new_value}")
        if new_value != self._current:
            self._current = new_value
            for w in self._additional_widgets.values():
                w.destroy()
            self._choose_setup()

