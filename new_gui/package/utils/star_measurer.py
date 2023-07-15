from subprocess import call
import shutil
import os
import numpy as np
from PIL import Image
import warnings
warnings.filterwarnings("error")


dss_cli_binary = "C:/Program Files/DeepSkyStacker (64 bit)/DeepSkyStackerCL.exe"
work_directory = "C:/Users/Florek/Desktop/workspace/PEliminator/new_gui/star_measurement"
template_file_path = "C:/Users/Florek/Desktop/workspace/PEliminator/new_gui/package/utils/star_measurement_list_template.txt"

test_input_path = "C:/Users/Florek/Desktop/workspace/PEliminator/new_gui/star_measurement/tests/light.tif"
test_input_ext = "tif"


class StarMeasurer:
    def __init__(self):
        self._detection_threshold = 45
        self._apply_median = True

    def set_detection_threshold_percent(self, percent):
        self._detection_threshold = max(min(99, percent), 1)

    def set_apply_median(self, new_value: bool):
        self._apply_median = new_value

    def measure_stars_on_np_array(self, array):
        im = Image.fromarray(array)
        measured_file_path = os.path.join(work_directory, f"light.tif")
        im.save(measured_file_path)
        return self._measure_stars()

    def _measure_stars(self):
        with open(template_file_path, "r") as f:
            template_lines = f.readlines()

        written_lines = []
        for t_line in template_lines:
            if "DetectionThreshold" in t_line:
                written_lines.append(
                    f"#WS#Software\DeepSkyStacker\Register|DetectionThreshold={self._detection_threshold}\n")
            elif "ApplyMedianFilter" in t_line:
                written_lines.append(
                    f"#WS#Software\DeepSkyStacker\Register|ApplyMedianFilter={1 if self._apply_median else 0}\n")
            else:
                written_lines.append(t_line)

        list_path = os.path.join(work_directory, "list.txt")
        with open(list_path, "w") as f:
            f.writelines(written_lines)

        dss_command = [dss_cli_binary, "/R", list_path]

        return_code = call(dss_command, shell=True)

        if return_code != 0:
            return -1

        info_file_path = os.path.join(work_directory, "light.Info.txt")
        with open(info_file_path, "r") as f:
            info_content = f.readlines()

        radiuses = [float(line.split("=")[-1]) for line in info_content if "MeanRadius" in line]
        try:
            average_radius = np.average(np.array(radiuses))
        except RuntimeWarning as rw:
            print("Failed star measurement")
            return -2
        return average_radius

    def measure_stars_on_file(self, input_image_path, input_extension):
        measured_file_path = os.path.join(work_directory, f"light.{input_extension}")
        shutil.copyfile(input_image_path, measured_file_path)
        return self._measure_stars()


if __name__ == "__main__":
    result = StarMeasurer().measure_stars_on_file(test_input_path, test_input_ext)
    print(f"Measured stars average radius = {result}")
