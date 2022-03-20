import os
import tkinter as tk
from tkinter import filedialog


# images_dir_mock = "C:/Users/Florek/Desktop/SharpCap Captures/2022-02-25/Capture/23_44_44"
# images_dir_mock = "C:/Users/Florek/Desktop/SharpCap Captures/2022-03-11/Capture/00_39_13"
images_dir_mock = None


class ImageFilesList:
    def __init__(self, frame, displayer, aggregator):
        self._dt_label = None
        self._files = None
        self._dir = None
        self._listbox = tk.Listbox(frame)
        self._displayer = displayer
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self._listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.BOTH)
        self._listbox.config(yscrollcommand=scrollbar.set)
        self._aggregator = aggregator
        self._files_relative = []

    def get_dir(self):
        return self._dir

    def _display_index(self, index):
        file_path = os.path.join(self._dir, self._files[index][0])
        self._displayer.display(file_path)
        return file_path

    def choose_dir(self):
        if images_dir_mock is None:
            self._dir = filedialog.askdirectory(title="Select directory with images:")
        else:
            self._dir = images_dir_mock
        print(f"Images dir = {self._dir}")
        self._files = [(f, os.path.getctime(os.path.join(self._dir, f))) for f in os.listdir(self._dir) if
                       ".fits" in f]
        t0 = self._files[0][1]
        self._files_relative = [f[1]-t0 for f in self._files]
        if not self._files:
            print("Could not find any fits images in given directory!")
            exit(0)
        print(f"Images = {self._files}")

        for name, _ in self._files:
            self._listbox.insert('end', name)

        self._listbox.pack(side=tk.LEFT)
        self._listbox.select_set(0)
        print(f"Read {len(self._files)} fits files")
        self._aggregator.push_files(self._files)
        self._display_index(0)

    def get_files_relative_time(self):
        return self._files_relative

    def show_datetime_on(self, label):
        self._dt_label = label
        if self._files:
            dt_text = "{:10.4f}".format(self._files[0][1])
            self._dt_label.configure(text=dt_text)

    def get_files_number(self):
        if not self._files:
            return None
        return len(self._files)

    def get_first_name(self):
        if self._files:
            return self._files[0][0]
        return None

    def _change_selection(self, index):
        self._listbox.selection_clear(0, tk.END)
        self._listbox.select_set(index)
        dt_text = "{:10.4f}".format(self._files[index][1])
        self._dt_label.configure(text=dt_text)

    def next(self):
        new_sel_ind = self._listbox.curselection()[0] + 1
        if new_sel_ind >= len(self._files):
            return None
        self._change_selection(new_sel_ind)
        return self._display_index(new_sel_ind)

    def display_selection(self):
        selection = self._listbox.curselection()
        if selection:
            sel_ind = selection[0]
            self._change_selection(sel_ind)
            self._display_index(sel_ind)

    def remove(self):
        selection = self._listbox.curselection()
        if selection:
            index = selection[0]
            self._listbox.delete(index)
            self._files.pop(index)
            print(f"Remained {len(self._files)} fits files")
