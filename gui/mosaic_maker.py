import os
import tkinter as tk
from tkinter import ttk
from astropy.io import fits
import numpy as np
from PIL import Image

from functions.widgets.dir_chooser import DirChooser, LabeledInput
from functions.widgets.application import SimpleGuiApplication

import glob
import subprocess
DETACHED_PROCESS = 8

dss_path = "C:\\Program Files\\DeepSkyStacker (64 bit)\\DeepSkyStackerCL.exe"


def execute_and_print(comm):
    with subprocess.Popen(comm,
                          stdout=subprocess.PIPE,
                          bufsize=1, universal_newlines=True) as p:
        for line in p.stdout:
            print(line, end='')


def call_dss_with_file_list(file_list_path, reference_path, result_name):
    print(f"Calling dss stacking for {file_list_path} into result {result_name} using {reference_path} as reference")
    """
    copy&paste from 
    https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
    """
    execute_and_print([dss_path, "/R", f"/O:{result_name}", file_list_path])
    print("Finished registration!")

    reference_path_info = reference_path.split(".fts")[0] + ".Info.txt"
    with open(reference_path_info, "r") as info:
        info_content = info.readlines()

    info_content[0] = "OverallQuality = 9999.99\n"

    with open(reference_path_info, "w") as info:
        info.writelines(info_content)
    print("Changed quality to enforce reference")

    execute_and_print([dss_path, "/S", f"/O:{result_name}", file_list_path])
    print("Finished stacking!")


def calculate_number_of_hstrips(span_y_as, increment_as):
    ret_val = int(span_y_as // increment_as)
    return ret_val


def split_image_in_horizontal_stripes(image_path, n, pad=0):
    with fits.open(image_path) as hdul:
        current_data = hdul[0].data

    print(f"n = {n}, pad ={pad}, im = {current_data.shape}")
    fragments = np.vsplit(np.pad(current_data, ((0, pad), (0, 0)), 'constant'), n)

    return {i: f for i, f in enumerate(reversed(fragments))}


out_map = {}


def save_fragments(fragments, index, out_dir):
    global out_map
    for i, f in fragments.items():
        total_index = i + index
        indices = [total_index]
        # indices = [total_index, total_index+1]
        # if total_index > 0:
        #     indices.insert(0, total_index-1)

        print(f"This will go into {indices} dirs")
        im = Image.fromarray(f)
        for k in indices:
            out_path = os.path.join(out_dir, f"strip_{k}")
            if k in out_map:
                out_map[k] += 1
            else:
                out_map[k] = 0

            path_to_save = os.path.join(out_path, f"{out_map[k]}.tif")
            print(f"Saving to {path_to_save}")
            im.save(path_to_save)


class MosaicMakerGUI(SimpleGuiApplication):
    def __init__(self, *args, **kwargs):
        super(MosaicMakerGUI, self).__init__(*args, **kwargs)

        self._input_chooser = DirChooser(frame=self._main_frame,
                                         dir_desc="Input images directory",
                                         initial_dir="C:\\Users\\Florek\\Desktop\\SharpCap Captures\\2022-10-17\\16_47_55"#os.getcwd()
                                         ).pack(side=tk.TOP)

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(
            side=tk.TOP, ipady=10, fill=tk.BOTH)
        self._images_per_list_input = LabeledInput(frame=self._main_frame, desc="Images per list", initial_value=24, from_=1, to=999, width=3)
        self._images_per_list_input.pack(side=tk.LEFT)

        self._split_button = ttk.Button(self._main_frame,
                                        style="B.TButton", text="Create lists", command=self._create_lists)
        self._split_button.pack(side=tk.LEFT)

        self._stack_button = ttk.Button(self._main_frame,
                                        style="B.TButton", text="Stack lists",
                                        command=self._stack_lists, state=tk.DISABLED)
        self._stack_button.pack(side=tk.LEFT)

        self._lists = []

    def _stack_lists(self):
        in_dir = self._input_chooser.get_dir()
        out_dir = os.path.join(in_dir, "output")
        for i, flist in enumerate(self._lists):#i in range(0, 1):
            print(flist)
            call_dss_with_file_list(*flist, f"result_file{i}")

    def _create_lists(self):
        in_dir = self._input_chooser.get_dir()
        out_dir = os.path.join(in_dir, "output")
        print(f"Using output dir as {out_dir}")
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)

        list_of_files = [f.replace("/", "\\") for f in glob.glob(os.path.join(in_dir, '*cal.fts'))]
        N = len(list_of_files)
        M = int(self._images_per_list_input.get_value()) // 2
        margin = M // 3
        print(f"N = {N}, M={M}, margin = {margin}")
        with open("template_image_list.txt", 'r') as template:
            template_str = str(template.read())
        if N > 0:
            refs = range(M, N, M)
            for r in refs:
                one_list = [i for i in range(max(0, r-M-margin), min(N-1, r+M+margin))]
                files = [(f, list_of_files[f]) for f in one_list]
                # print(f"For ref = {r} list = {files}")
                new_list = []
                new_list.append(f"1\treflight\t{list_of_files[r]}")
                for i, f in files:
                    if i != r:
                        new_list.append(f"1\tlight\t{f}")

                new_list_nls="\n".join(new_list)
                new_file_content = template_str.replace("<<list>>", new_list_nls)
                print(new_file_content)
                print("======================\n")
                new_list_name = f"list_{r}.txt"
                new_list_path = os.path.join(out_dir, new_list_name)
                with open(new_list_path, "w") as out_list:
                    out_list.write(new_file_content)

                self._lists.append((new_list_path, list_of_files[r]))

            self._stack_button.configure(state=tk.NORMAL)


    def _split(self):
        print("Starting to split...")

        # Some calculations that need to take configuration:
        increment_as = 62*15
        print(f"Increment in as = {increment_as}")
        res_x = 1608
        res_y = 1104
        focal_mm = 135
        pixel_um = 9
        scale = pixel_um * 206.25 / focal_mm
        span_y_as = res_y * scale
        number_of_strips = calculate_number_of_hstrips(span_y_as, increment_as)
        size_of_strip = int(res_y // number_of_strips)

        print(f"Size of strip is {size_of_strip} px")
        total_size = number_of_strips*size_of_strip
        print(f"Total size of strips is {total_size} px")
        missing = total_size - res_y
        print(f"Missing is {missing} px")
        ###########################



        in_dir = self._input_chooser.get_dir()
        out_dir = self._output_chooser.get_dir()
        if in_dir == out_dir:
            print("It is not advised to use same dir as input and output!")
            return

        if out_dir == os.getcwd():
            out_dir = os.path.join(in_dir, "output")
            print(f"Using output dir as {out_dir}")
            if not os.path.isdir(out_dir):
                os.mkdir(out_dir)

        list_of_files = glob.glob(os.path.join(in_dir, '*cal.fts'))

        number_of_files = len(list_of_files)


        number_of_stacks = int(number_of_files + number_of_strips)
        strip_dirs = {i: os.path.join(out_dir, f"strip_{i}") for i in range(0, number_of_stacks)}
        for d in strip_dirs.values():
            if not os.path.isdir(d):
                os.mkdir(d)

        # start_coords = plate_solve(list_of_files[0])
        for i, f in enumerate(list_of_files):
            fragments = split_image_in_horizontal_stripes(f, n=number_of_strips, pad=missing)
            save_fragments(fragments, i, out_dir)


gui = MosaicMakerGUI(geometry="640x480")
gui.run()
