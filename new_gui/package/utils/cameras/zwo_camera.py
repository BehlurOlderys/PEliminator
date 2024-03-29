from package.ascom.ascom_camera import AscomCamera, CameraState
import zwoasi as asi
import numpy as np
import base64
import os
from PIL import Image
import logging


def add_log(name):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    main_handler = logging.FileHandler(name+".log")
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(filename)s %(funcName)s(%(lineno)d) -- %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    main_handler.setFormatter(formatter)
    log.addHandler(main_handler)
    return log


if os.name == "nt": 
    asi_lib_path = "C:\\ASI SDK\\lib\\x64\\ASICamera2.dll"
else:
    asi_lib_path = "/usr/local/lib/libASICamera2.so.1.27"
asi_initialized = False

ONE_SECOND_IN_MILLISECONDS = 1000
ONE_MILLISECOND_IN_MICROSECONDS = 1000
ONE_SECOND_IN_MICROSECONDS = ONE_SECOND_IN_MILLISECONDS * ONE_MILLISECOND_IN_MICROSECONDS


exp_states = {
    asi.ASI_EXP_IDLE: "Idle",
    asi.ASI_EXP_FAILED: "Failed",
    asi.ASI_EXP_SUCCESS: "Success",
    asi.ASI_EXP_WORKING: "Working"
}

image_types_by_name = {
    "RAW8": asi.ASI_IMG_RAW8,
    "RGB24": asi.ASI_IMG_RGB24,
    "RAW16": asi.ASI_IMG_RAW16,
    "Y8": asi.ASI_IMG_Y8
}

image_types_by_value = {v: k for k, v in image_types_by_name.items()}


logs = {}


class ZwoCamera(AscomCamera):
    def __init__(self, camera_index):
        if camera_index not in logs.keys():
            logs[camera_index] = add_log(f"camera_{camera_index}")

        self._log = logs[camera_index]
        self._state = CameraState.IDLE
        self._camera = asi.Camera(camera_index)
        self._index = camera_index
        # self._camera.set_control_value(asi.ASI_HIGH_SPEED_MODE, 0)
        self._camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, 40)
        self._camera.set_control_value(asi.ASI_GAIN, 17)
        self._camera.set_control_value(asi.ASI_EXPOSURE, 1 * ONE_SECOND_IN_MICROSECONDS)
        supported = self._camera.get_camera_property()['SupportedVideoFormat']
        self._camera.set_image_type(supported[0])
        self._connected = True
        self._new_filename = None
        self._last_duration = 1
        self._log.info(f"ROI FORMAT = {self._camera.get_roi_format()}")

        self._buffer = None
        self._buffer_size = 0
        self._reserve_buffer()

    def set_exposure(self, duration_s):
        duration_s = float(duration_s)
        self._camera.set_control_value(asi.ASI_EXPOSURE, int(duration_s * ONE_SECOND_IN_MICROSECONDS))
        self._last_duration = duration_s

    def capture(self, filename):
        try:
            self._camera.capture(filename=filename)
            return True
        except asi.ZWO_CaptureError as ce:
            print(f"error = {ce}, status = {ce.exposure_status}")
            return False

    def _reserve_buffer(self):
        whbi = self._camera.get_roi_format()
        sz = whbi[0] * whbi[1]
        if whbi[3] == asi.ASI_IMG_RGB24:
            sz *= 3
        elif whbi[3] == asi.ASI_IMG_RAW16:
            sz *= 2
        self._log.info(f"Reserving buffer of size {whbi[0]}x{whbi[1]}={sz}")

        if self._buffer is None:
            self._buffer_size = sz
            self._buffer = bytearray(sz)
            return

        if sz != self._buffer_size:
            del self._buffer
            self._buffer_size = sz
            self._buffer = bytearray(sz)

    def _get_buffer(self):
        return self._buffer, self._buffer_size

    def _store_imagebytes(self):
        self._camera.get_data_after_exposure(self._buffer)

    def get_imagebytes(self):
        self._store_imagebytes()
        return self._get_buffer()

    def is_image_failed(self):
        return self._camera.get_exposure_status() == 3

    def is_camera_idle(self):
        return self._camera.get_exposure_status() == 0

    def get_np_array_from_buffer(self, buffer):
        whbi = self._camera.get_roi_format()
        shape = [whbi[1], whbi[0]]
        if whbi[3] == asi.ASI_IMG_RAW8 or whbi[3] == asi.ASI_IMG_Y8:
            img = np.frombuffer(buffer, dtype=np.uint8)
        elif whbi[3] == asi.ASI_IMG_RAW16:
            img = np.frombuffer(buffer, dtype=np.uint16)
        elif whbi[3] == asi.ASI_IMG_RGB24:
            img = np.frombuffer(buffer, dtype=np.uint8)
            shape.append(3)
        else:
            raise ValueError('Unsupported image type')
        img = img.reshape(shape)
        if len(img.shape) == 3:
            img = img[:, :, ::-1]  # Convert BGR to RGB
        return img

    def save_image_to_file(self, filename):
        self._store_imagebytes()
        whbi = self._camera.get_roi_format()
        shape = [whbi[1], whbi[0]]
        if whbi[3] == asi.ASI_IMG_RAW8 or whbi[3] == asi.ASI_IMG_Y8:
            img = np.frombuffer(self._buffer, dtype=np.uint8)
        elif whbi[3] == asi.ASI_IMG_RAW16:
            img = np.frombuffer(self._buffer, dtype=np.uint16)
        elif whbi[3] == asi.ASI_IMG_RGB24:
            img = np.frombuffer(self._buffer, dtype=np.uint8)
            shape.append(3)
        else:
            raise ValueError('Unsupported image type')
        img = img.reshape(shape)

        mode = None
        if len(img.shape) == 3:
            img = img[:, :, ::-1]  # Convert BGR to RGB


        if whbi[3] == asi.ASI_IMG_RAW16:
            mode = 'I;16'
        image = Image.fromarray(img, mode=mode)
        image.save(filename)
        self._log.debug('wrote %s', filename)

    def save_to_file_and_get_imagebytes(self, filename):
        self.save_image_to_file(filename)
        return self._get_buffer()

    def get_image_specs(self):
        """
        :return: tuple with elements:
        rank, dim0, dim1, dim2
        """
        whbi = self._camera.get_roi_format()
        im_type = whbi[3]
        if im_type in [asi.ASI_IMG_RAW8, asi.ASI_IMG_Y8, asi.ASI_IMG_RAW16]:
            rank = 2
        elif im_type == asi.ASI_IMG_RGB24:
            rank = 3
        else:
            return -1
        dim3 = 0 if rank == 2 else 3
        return rank, whbi[0], whbi[1], dim3

    def get_property(self):
        return self._camera.get_camera_property()

    def get_controls(self):
        return self._camera.get_controls()

    @staticmethod
    def get_cameras_list():
        if not asi_initialized:
            raise RuntimeError("ASI library not initialized")
        if asi.get_num_cameras() == 0:
            return []
        return asi.list_cameras()

    @staticmethod
    def initialize_library():
        global asi_initialized
        if not asi_initialized:
            asi.init(asi_lib_path)
            asi_initialized = True

    # General ASCOM device methods:
    def get_connected(self):
        return self._connected

    def set_connected(self, value):
        value = bool(value)
        if self._connected and not value:
            del self._camera
            self._connected = False
        elif not self._connected and value:
            self._camera = asi.Camera(self._index)
            self._connected = True

    def get_name(self):
        return self._camera.get_camera_property()["Name"]

    def get_description(self):
        if "Description" in self._camera.get_camera_property():
            return self._camera.get_camera_property()["Description"]
        return "<no description available>"

    def get_driverinfo(self):
        return "This is ALPACA driver by Bartlomiej Hnatio"

    def get_driverversion(self):
        return "v1.0"

    def get_interfaceversion(self):
        return 1

    def get_supportedactions(self):
        return []

    # Camera specific methods - as required by Sharpcap (for now) # TODO!

    def get_canpulseguide(self):
        return False  # TODO as for now

    def get_canfastreadout(self):
        return "HighSpeedMode" in self._camera.get_controls()

    def get_sensorname(self):
        return self._camera.get_camera_property()["Name"]

    def get_pixelsizex(self):
        return self._camera.get_camera_property()["PixelSize"]

    def get_pixelsizey(self):
        return self._camera.get_camera_property()["PixelSize"]

    def get_cameraxsize(self):
        return self._camera.get_camera_property()["MaxWidth"]

    def get_cameraysize(self):
        return self._camera.get_camera_property()["MaxHeight"]

    def get_canasymmetricbin(self):
        return False

    def get_binx(self):
        return self._camera.get_bin()

    def get_biny(self):
        return self._camera.get_bin()

    def get_ccdtemperature(self):
        return float(self._camera.get_control_value(asi.ASI_TEMPERATURE)[0]) / 10.0

    def set_gain(self, value):
        value = int(value)
        self._camera.set_control_value(asi.ASI_GAIN, value)

    def get_bayeroffsetx(self):
        return 0  # TODO!

    def get_bayeroffsety(self):
        return 0  # TODO!

    def get_camerastate(self):
        exp_status = self._camera.get_exposure_status()
        if exp_status == 2:
            return CameraState.IDLE
        if exp_status == 3:
            return CameraState.ERROR
        if exp_status == 0:
            return CameraState.IDLE
        if exp_status == 1:
            return CameraState.EXPOSING

        return CameraState.WAITING  # TODO: for sure?
        # IDLE = 0
        # WAITING = 1
        # EXPOSING = 2
        # READING = 3
        # DOWNLOAD = 4
        # ERROR = 5
        #
        # ASI_EXP_IDLE = 0
        # ASI_EXP_WORKING = 1
        # ASI_EXP_SUCCESS = 2
        # ASI_EXP_FAILED = 3

    def get_canabortexposure(self):
        return False  # TODO - maybe?

    def get_cangetcoolerpower(self):
        return False

    def get_cansetccdtemperature(self):
        return self._camera.get_camera_property()["IsCoolerCam"]

    def get_canstopexposure(self):
        return False  # TODO! Maybe it can be done

    def get_cooleron(self):
        return False

    def get_coolerpower(self):
        pass  # TODO!

    def get_electronsperadu(self):
        pass  # TODO!

    def get_exposuremax(self):
        return self._camera.get_controls()["Exposure"]["MaxValue"] / ONE_SECOND_IN_MICROSECONDS

    def get_exposuremin(self):
        return self._camera.get_controls()["Exposure"]["MinValue"] / ONE_SECOND_IN_MICROSECONDS

    def get_exposureresolution(self):
        return 1.0 / ONE_SECOND_IN_MICROSECONDS

    def get_fastreadout(self):
        return self._camera.get_controls().get("HighSpeedMode", 0)

    def get_fullwellcapacity(self):
        pass  # TODO!

    def get_gain(self):
        return self._camera.get_control_value(asi.ASI_GAIN)[0]

    def get_gainmax(self):
        return self._camera.get_controls()["Gain"]["MaxValue"]

    def get_gainmin(self):
        return self._camera.get_controls()["Gain"]["MinValue"]

    def get_gains(self):
        pass  # TODO!

    def get_hasshutter(self):
        pass  # TODO!

    def get_heatsinktemperature(self):
        return 0  # TODO!!!

    def get_imagearray(self):
        filename = self._new_filename  # TODO this can be somehow customized
        data = self._camera.get_data_after_exposure(None)

        whbi = self._camera.get_roi_format()

        shape = [whbi[1], whbi[0]]
        if whbi[3] == asi.ASI_IMG_RAW8 or whbi[3] == asi.ASI_IMG_Y8:
            img = np.frombuffer(data, dtype=np.uint8)
        elif whbi[3] == asi.ASI_IMG_RAW16:
            img = np.frombuffer(data, dtype=np.uint16)
        elif whbi[3] == asi.ASI_IMG_RGB24:
            img = np.frombuffer(data, dtype=np.uint8)
            shape.append(3)
        else:
            raise ValueError('Unsupported image type')
        img = img.reshape(shape)
        # img = np.transpose(img, (1, 0, 2))

        # if filename is not None:
        #     mode = None
        #     if len(img.shape) == 3:
        #         img = img[:, :, ::-1]  # Convert BGR to RGB
        #     if whbi[3] == asi.ASI_IMG_RAW16:
        #         mode = 'I;16'
        #     image = Image.fromarray(img, mode=mode)
        #     image.save(filename)
        #     log.debug('wrote %s', filename)
        return img, filename

    def get_imagearraybase64(self):
        img = self.get_imagearray()
        base64_bytes = base64.b64encode(img)
        return base64_bytes.decode('ascii')

    def get_imagearrayvariant(self):
        pass  # TODO!

    def get_imageready(self):
        return self._camera.get_exposure_status() == 2

    def get_ispulseguiding(self):
        pass  # TODO!

    def get_lastexposureduration(self):
        return self._last_duration

    def get_lastexposurestarttime(self):
        pass  # TODO!

    def get_maxadu(self):
        return 2**(self._camera.get_camera_property()["BitDepth"])

    def get_maxbinx(self):
        return max(self._camera.get_camera_property()["SupportedBins"])

    def get_maxbiny(self):
        return max(self._camera.get_camera_property()["SupportedBins"])

    def get_numx(self):
        return self._camera.get_roi_format()[0]

    def get_numy(self):
        return self._camera.get_roi_format()[1]

    def get_offset(self):
        pass  # TODO!

    def get_offsetmax(self):
        pass  # TODO!

    def get_offsetmin(self):
        pass  # TODO!

    def get_offsets(self):
        pass  # TODO!

    def get_percentcompleted(self):
        pass  # TODO!

    def get_readoutmode(self):
        camera_info = self._camera.get_camera_property()
        supported = camera_info['SupportedVideoFormat']
        sorted_supported = [s for s in sorted(supported)]
        mode = self._camera.get_image_type()
        return sorted_supported.index(mode)

    def get_readoutmodes(self):
        camera_info = self._camera.get_camera_property()
        supported = camera_info['SupportedVideoFormat']
        print(f"Supported = {supported}")
        return [image_types_by_value[s] for s in sorted(supported)]

    def get_sensortype(self):
        # if not self._camera.get_camera_property()["IsColorCam"]:
        #     return 0
        # return self._camera.get_camera_property()["BayerPattern"]
        return 2  # TODO!!!! it should be variable, this is good only for ASI120MC

    def get_setccdtemperature(self):
        pass  # TODO!

    def get_startx(self):
        return self._camera.get_roi()[0]

    def get_starty(self):
        return self._camera.get_roi()[1]

    def _set_bins(self, value):
        whbi = self._camera.get_roi_format()
        new_bins = int(value)
        if new_bins < 0 or new_bins > max(self._camera.get_camera_property()["SupportedBins"]):
            raise Exception

        old_bins = whbi[2]
        whbi[0] = int(whbi[0]*old_bins/new_bins)
        whbi[1] = int(whbi[1]*old_bins/new_bins)
        whbi[2] = new_bins

        self._camera.set_roi_format(*whbi)

    def set_readoutmode_str(self, strvalue):
        self._camera.set_image_type(image_types_by_name[strvalue])
        self._reserve_buffer()

    def set_readoutmode(self, value):
        value = int(value)
        camera_info = self._camera.get_camera_property()
        supported = camera_info['SupportedVideoFormat']

        # list like "RGB8, RAW16"
        used_list = [image_types_by_value[s] for s in sorted(supported)]

        # value of 1 means RAW16 in above example
        image_type_name = used_list[value]

        # finally translate name into camera index and change:
        self._camera.set_image_type(image_types_by_name[image_type_name])
        self._reserve_buffer()

    def set_binx(self, value):
        value = int(value)
        self._set_bins(value)
        self._reserve_buffer()

    def set_biny(self, value):
        self._set_bins(value)
        self._reserve_buffer()

    def set_numx(self, value):
        value = int(value)
        sx, sy, _, h = self._camera.get_roi()
        self._camera.set_roi(sx, sy, value, h)
        self._reserve_buffer()

    def set_numy(self, value):
        value = int(value)
        sx, sy, w, _ = self._camera.get_roi()
        self._camera.set_roi(sx, sy, w, value)
        self._reserve_buffer()

    def set_startx(self, value):
        value = int(value)
        _, sy, w, h = self._camera.get_roi()
        self._camera.set_roi(value, sy, w, h)
        self._reserve_buffer()

    def set_starty(self, value):
        value = int(value)
        sx, _, w, h = self._camera.get_roi()
        self._camera.set_roi(sx, value, w, h)
        self._reserve_buffer()

    def abortexposure(self):
        pass  # TODO!

    def stopexposure(self):
        self._camera.stop_exposure()

    def startexposure(self, duration, light=True, save=False):
        duration = float(duration)
        exposure_us = int(duration * ONE_SECOND_IN_MICROSECONDS)
        self._log.info(f"Starting exposure: {exposure_us}us")
        if self._last_duration != duration:
            self._last_duration = duration
            self._camera.set_control_value(asi.ASI_EXPOSURE, exposure_us)
        self._camera.start_exposure(is_dark=not light)
