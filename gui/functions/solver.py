import os
import platform
import itertools
import tkinter as tk
from tkinter import ttk
from common import global_settings
from solver_impls import ASPSSolver


solvers_to_check = [ASPSSolver.dir_name()]
regular_pf_path = os.environ["ProgramW6432"]
pf_path_86 = os.environ["ProgramFiles(x86)"]
paths_to_check = [regular_pf_path, pf_path_86]
solver_instances = {}
solver_ctors = {ASPSSolver.dir_name(): ASPSSolver}

image1_coordinates = "08:22:56, 24:59:50"
image2_coordinates = "05:22:45, 33:27:31"


def check_for_solver(directory, s):
    possible_dirs = [d for d in os.listdir(directory)]
    if s in possible_dirs:
        return s, os.path.join(directory, s)
    return None


def get_plate_solvers_paths():
    system_name = platform.system()
    if system_name != 'Windows':
        print(f"This cannot run on platform {system_name}!")
        return None

    items_to_check = itertools.product(paths_to_check, solvers_to_check)
    return dict(filter(None, [check_for_solver(p, s) for p, s in items_to_check]))


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


def choose_solver():
    solvers = get_plate_solvers_paths()
    print(f"Available solvers are: {solvers}")
    return SolverChoice(solvers).get_chosen()


def get_solver_instance(solver_choice):
    solver_name, solver_path = solver_choice
    if not (solver_name in solver_instances):
        ctor = solver_ctors[solver_name]
        solver_instances[solver_name] = ctor(global_settings.settings, solver_path)

    return solver_instances[solver_name]


so = choose_solver()
si = get_solver_instance(so)
si.blind_solve("image2.fits")
si.check_output()
