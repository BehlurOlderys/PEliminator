import subprocess
import os

ASPS_solver_output_file_name = "../last_solve.dat"
ASPS_solver_dir_name = "PlateSolver"
ASPS_solver_exe_name = "PlateSolver.exe"


def convert_as_to_dms(arcseconds):
    s = arcseconds % 60
    d = arcseconds // 3600
    m = (arcseconds - d * 3600) // 60
    return d, m, s


class ASPSSolver:
    def __init__(self, settings, executable_path):
        self._settings = settings
        self._exec = os.path.join(executable_path, ASPS_solver_exe_name)
        self._output_name = ASPS_solver_output_file_name

    @staticmethod
    def output_file_name():
        return ASPS_solver_output_file_name

    @staticmethod
    def dir_name():
        return ASPS_solver_dir_name

    def blind_solve(self, path):
        f = self._settings.get_focal_length()
        p = self._settings.get_pixel_pitch()

        command = [self._exec,
                   "/solvefile",
                   os.path.join(os.getcwd(), path),
                   os.path.join(os.getcwd(), self._output_name),  # Output file
                   str(f),
                   str(p)]

        print(f"Command = {command}")
        ret = subprocess.check_output(command)
        print(ret)

        # PlateSolver.exe /solvefile < FileName > < OutputFile > [ < FocalLength >] [ < PixelSize >] [ < CurrentRA >]
        # [ < CurrentDec >] [ < NearRadius >]

    def check_output(self):
        with open(os.path.join(os.getcwd(), self._output_name), 'r') as f:
            lines = f.readlines()

        if 'OK' in lines[0]:
            print(f"Plate solving successful!")

        else:
            return

        ra_num = float(lines[1])
        dec_num = float(lines[2])

        ra_h, ra_m, ra_s = convert_as_to_dms(int(ra_num * 3600 / 15))
        dec_d, dec_m, dec_s = convert_as_to_dms(int(dec_num * 3600))

        print(f"{ra_h}:{ra_m}:{ra_s}, {dec_d}:{dec_m}:{dec_s}")
