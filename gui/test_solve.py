import os
import platform
import itertools
import subprocess
import tkinter as tk
from tkinter import ttk

solver_output_file_name = "last_solve.dat"
ASPS_solver_dir_name = "PlateSolver"
solvers_to_check = [ASPS_solver_dir_name]

regular_pf_path = os.environ["ProgramW6432"]
pf_path_86 = os.environ["ProgramFiles(x86)"]
paths_to_check = [regular_pf_path, pf_path_86]

execs_names = {ASPS_solver_dir_name: "PlateSolver.exe"}


image1_coordinates = "08:22:56, 24:59:50"
image2_coordinates = "05:22:45, 33:27:31"


def check_for_solver(directory, s):
    possible_dirs = [d for d in os.listdir(directory)]
    if s in possible_dirs:
        return s, os.path.join(directory, s, execs_names[s])
    return None


def get_plate_solvers_paths():
    system_name = platform.system()
    if system_name != 'Windows':
        print(f"This cannot run on platform {system_name}!")
        return None

    items_to_check = itertools.product(paths_to_check, solvers_to_check)
    return dict(filter(None, [check_for_solver(p, s) for p, s in items_to_check]))


class Settings:
    def __init__(self):
        self._focal = 650
        self._pixel = 2.9

    def get_focal_length(self):
        return self._focal

    def get_pixel_pitch(self):
        return self._pixel


class ASPS_Proxy:
    def __init__(self, settings, exec):
        self._settings = settings
        self._exec = exec

    def blind_solve(self, path):
        f = self._settings.get_focal_length()
        p = self._settings.get_pixel_pitch()

        command = [self._exec,
                   "/solvefile",
                   os.path.join(os.getcwd(), path),
                   os.path.join(os.getcwd(), solver_output_file_name),  # Output file
                   str(f),
                   str(p)]

        print(f"Command = {command}")
        ret = subprocess.check_output(command)
        print(ret)

        # PlateSolver.exe /solvefile < FileName > < OutputFile > [ < FocalLength >] [ < PixelSize >] [ < CurrentRA >]
        # [ < CurrentDec >] [ < NearRadius >]


class SolverChoice:
    def __init__(self, choices):
        self._root = tk.Tk()
        self._root.title("Choose plate solver")

        self._buttons_frame = tk.Frame(self._root)
        self._buttons_frame.pack(side=tk.BOTTOM, expand=True)

        self._ok_button = tk.Button(self._buttons_frame, text="OK", command=self.accept_choice)
        self._ok_button.pack(side=tk.LEFT)

        self._cancel_button = tk.Button(self._buttons_frame, text="Cancel", command=self.cancel_choice)
        self._cancel_button.pack(side=tk.RIGHT)

        self._choices = choices
        self._combo = ttk.Combobox(self._root)
        values = list(choices.keys())
        self._combo['values'] = values
        self._combo.set(values[0])
        self._combo.pack(side=tk.TOP, expand=True)
        self._chosen_one = None
        self._root.geometry('250x50')

    def accept_choice(self):
        key = self._combo.get()
        self._chosen_one = (key, self._choices[key])
        print(f"Chosen = {self._chosen_one}")
        self._root.destroy()

    def cancel_choice(self):
        self._chosen_one = None
        self._root.destroy()

    def get_chosen(self):
        self._root.mainloop()
        return self._chosen_one


settings = Settings()
solvers = get_plate_solvers_paths()
print(f"Available solvers are: {solvers}")

solver_choice = SolverChoice(solvers).get_chosen()
if solver_choice is None:
    exit(0)

solver_name, solver_exec = solver_choice
solver_factories = {ASPS_solver_dir_name: ASPS_Proxy}
proxy = solver_factories[solver_name](settings, solver_exec)
proxy.blind_solve("image2.fits")


def convert_as_to_dms(arcseconds):
    s = arcseconds % 60
    d = arcseconds // 3600
    m = (arcseconds - d * 3600) // 60
    return d, m, s


def check_ASPS_output():
    with open(os.path.join(os.getcwd(), solver_output_file_name), 'r') as f:
        lines = f.readlines()

    if 'OK' in lines[0]:
        print(f"Plate solving successful!")

    else:
        return

    ra_num = float(lines[1])
    dec_num = float(lines[2])

    ra_h, ra_m, ra_s = convert_as_to_dms(int(ra_num * 3600 / 15))
    dec_d, dec_m, dec_s = convert_as_to_dms(int(dec_num*3600))

    print(f"{ra_h}:{ra_m}:{ra_s}, {dec_d}:{dec_m}:{dec_s}")


check_ASPS_output()
