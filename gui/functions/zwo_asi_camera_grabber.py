import zwoasi as asi
import matplotlib.pyplot as plt


asi_lib_path = "C:\\ASI SDK\\lib\\x64\\ASICamera2.dll"
asi_initialized = False


class ASICamera:
    def __init__(self, camera_index):
        self._camera = asi.Camera(camera_index)

    @staticmethod
    def get_cameras_list():
        if asi.get_num_cameras() == 0:
            return []
        return asi.list_cameras()

    @staticmethod
    def initialize_library():
        global asi_initialized
        if not asi_initialized:
            asi.init(asi_lib_path)
            asi_initialized = True

    def get_controls(self):
        return self._camera.get_controls()

    def connect_and_prepare_camera(self, exposure_ms=50, gain=0, roi=(256, 512)):
        camera_info = self._camera.get_camera_property()
        print(camera_info)
        # Use minimum USB bandwidth permitted
        self._camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, 40)
        print(f"HS = {self._camera.get_control_value(asi.ASI_HIGH_SPEED_MODE)}")
        controls = self._camera.get_controls()
        for cn in sorted(controls.keys()):
            print('    %s:' % cn)
            for k in sorted(controls[cn].keys()):
                print('        %s: %s' % (k, repr(controls[cn][k])))
        # Set ROI
        if roi is not None:
            image_w, image_h = roi
            start_x = (camera_info["MaxWidth"] - image_w) // 2
            start_y = (camera_info["MaxHeight"] - image_h) // 2
            image_w = image_w
            image_h = image_h
            print(f"ROI = {start_x}, {start_y}")
            self._camera.set_roi(start_x=start_x, start_y=start_y, width=image_w, height=image_h)
        self._camera.set_image_type(asi.ASI_IMG_RAW16)
        self._camera.set_control_value(asi.ASI_GAIN, gain)
        self._camera.set_control_value(asi.ASI_EXPOSURE, exposure_ms*1000)  # us

    def get_camera_temperature(self):
        return float(self._camera.get_control_value(asi.ASI_TEMPERATURE)[0]) / 10.0

    def capture_file(self, filename):
        try:
            self._camera.capture(filename=filename)
            return True
        except asi.ZWO_CaptureError as ce:
            print(f"error = {ce}, status = {ce.exposure_status}")
            return False

    def capture_image(self):
        return self._camera.capture()


def ask_user_for_camera_to_choose(list_of_cameras):
    choice = -1
    while choice < 0 or choice >= len(list_of_cameras):
        print(f"Choose camera by pressing number and hitting Enter key:")
        list_to_display = "".join([f"[{i}]: {c}\n" for i, c in enumerate(list_of_cameras)])
        print(list_to_display)
        choice = int(input())
    return choice


if __name__ == "__main__":
    """
    Some of the code is taken from examples:
    https://github.com/python-zwoasi/python-zwoasi/blob/master/zwoasi/examples/zwoasi_demo.py
    """

    asi_camera = ASICamera()
    # camera_id = ask_user_for_camera_to_choose(asi_camera.get_cameras_list())
    camera_id = 0
    asi_camera.connect_and_prepare_camera(camera_id=camera_id)

    image_buffer = asi_camera.capture_image()
    plt.imshow(image_buffer)
    plt.show()
