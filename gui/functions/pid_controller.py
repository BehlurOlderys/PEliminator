from functions.spin_with_label import SpinWithLabel
import tkinter as tk


class MyPID:
    def __init__(self, kp, ki, kd, isize, **_):
        self._kp_var = kp
        self._ki_var = ki
        self._kd_var = kd
        self._memory = [0]
        self._memory_size_var = isize
        print(f"Initializing PID with Kp={self._kp_var.get()},"
              f" Ki={self._ki_var.get()}, Kd={self._kd_var.get()} and size of {self._memory_size_var.get()}")

    def get_correction(self, error):
        diff_d = error-self._memory[-1]
        memory_size = int(self._memory_size_var.get())
        self._memory.append(error)
        while len(self._memory) >= memory_size:
            self._memory.pop(0)

        sum_i = sum(self._memory)
        try:
            return float(self._kp_var.get()) * error + \
                   float(self._ki_var.get()) * sum_i + \
                   float(self._kd_var.get()) * diff_d
        except ValueError:
            return 0


def filter_dict_for_prefix_to_pid(d, prefix):
    return {k.split("_")[-1]: v for k, v in d.items() if prefix in k}


class PIDGUI:
    def __init__(self, frame, prefix, vars_dict, label):
        self._kp_var = tk.StringVar(value=0.5)
        self._ki_var = tk.StringVar(value=0.15)
        self._kd_var = tk.StringVar(value=0.0)
        self._isize_var = tk.StringVar(value=12)

        vars_dict.update({
            prefix+"_kp": self._kp_var,
            prefix+"_ki": self._ki_var,
            prefix+"_kd": self._kd_var,
            prefix+"_isize": self._isize_var
        })

        self._label = tk.Label(frame, text=label, font=('calibre', 10, 'bold'))
        self._label.pack(side=tk.LEFT)

        self._kp_indicator = SpinWithLabel(
            frame, self._kp_var, "Kp=", format="%.3f", increment=0.01, width=5, from_=0, to=10.0)
        self._ki_indicator = SpinWithLabel(
            frame, self._ki_var, "Ki=", format="%.3f", increment=0.01, width=5, from_=0, to=10.0)
        self._kd_indicator = SpinWithLabel(
            frame, self._kd_var, "Kd=", format="%.3f", increment=0.01, width=5, from_=0, to=10.0)
        self._isize_indicator = SpinWithLabel(
            frame, self._isize_var, "i_size=", increment=1, width=3, from_=2, to=20)
