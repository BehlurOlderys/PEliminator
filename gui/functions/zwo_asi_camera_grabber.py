import zwoasi as asi
import matplotlib.pyplot as plt


asi_lib_path = "C:\\ASI SDK\\lib\\x64\\ASICamera2.dll"


class ASICamera:
    def __init__(self):
        self._camera = None

    def get_cameras_list(self):
        if asi.get_num_cameras() == 0:
            return []
        return asi.list_cameras()

    def connect_and_prepare_camera(self, camera_id=0, exposure_ms=50, gain=0, roi=(256, 512)):
        asi.init(asi_lib_path)
        self._camera = asi.Camera(camera_id)
        camera_info = self._camera.get_camera_property()
        print(camera_info)
        # Use minimum USB bandwidth permitted
        self._camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD,
                                       self._camera.get_controls()['BandWidth']['MinValue'])

        controls = self._camera.get_controls()
        for cn in sorted(controls.keys()):
            print('    %s:' % cn)
            for k in sorted(controls[cn].keys()):
                print('        %s: %s' % (k, repr(controls[cn][k])))
        # Set ROI
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
