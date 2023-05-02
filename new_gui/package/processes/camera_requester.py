import requests
import json
import time
from datetime import datetime
from PIL import Image
import io
from package.ascom.ascom_camera import CameraState


default_format = "%Y-%m-%d %H:%M:%S.%f"


def get_diff_ms(a, b):
    return (a - b).total_seconds() * 1000


ascom_states = {
    int(CameraState.IDLE): "IDLE",
    int(CameraState.WAITING): "WAITING",
    int(CameraState.EXPOSING): "EXPOSING",
    int(CameraState.READING): "READING",
    int(CameraState.DOWNLOAD): "DOWNLOAD",
    int(CameraState.ERROR): "ERROR",
}


class RequestCounter:
    def __init__(self):
        self._counter = 0

    def get_new_count(self):
        cc = self._counter
        self._counter += 1
        return cc


class AscomRequests:
    def __init__(self, address="http://localhost:8080", counter=RequestCounter(), cid=0):
        self._address = address + "/api/v1/"
        self._rc = counter
        self._cid = cid

    def update_address(self, address):
        old_address_suffix = "/".join(self._address.split(":")[-1].split("/")[1:])
        new_address = address + "/" + old_address_suffix
        self._address = new_address
        print(f"New address = {self._address}")

    def _get_common_query(self):
        return {"ClientID": self._cid, "ClientTransactionID": self._rc.get_new_count()}


class CameraRequests(AscomRequests):
    def __init__(self, camera_no, **kwargs):
        super(CameraRequests, self).__init__(**kwargs)
        self._camera_no = camera_no
        self._append_address()

    def put_start_continuous_imaging(self):
        return self._put_request(endpoint="startcontinuous")

    def put_stop_continuous_imaging(self):
        return self._put_request(endpoint="stopcontinuous")

    def _append_address(self):
        self._camera_address = self._address + f"camera/{self._camera_no}"

    def update_address(self, address):
        super(CameraRequests, self).update_address(address)
        self._append_address()
        print(f"Using camera address: {self._camera_address}")

    def _get_request(self, endpoint, query_params=None, headers=None, stream=False):
        gui_before = datetime.now()
        print(f"GET request for {self._camera_address}/{endpoint}...")
        headers = headers if headers else {}
        query = self._get_common_query()
        if query_params is not None:
            query.update(query_params)
        r = requests.get(f"{self._camera_address}/{endpoint}", params=query, headers=headers, stream=stream)
        gui_after = datetime.now()
        print(f"...returned code {r.status_code}")
        if r.status_code == 200:
            print(f"Received 200 with headers: {r.headers}")
            timestamps = json.loads(r.headers['Timestamps'])
            print(f"Timestamps = {timestamps}")

            server_before = datetime.strptime(timestamps["before"], default_format)
            server_after = datetime.strptime(timestamps["after"], default_format)

            ms_bc = get_diff_ms(server_after, server_before)
            ms_total = get_diff_ms(gui_after, gui_before)
            print(f"server time={ms_bc}ms, total={ms_total}ms")

        return r

    def _get_image_from_stream(self, **kwargs):
        CHUNK_SIZE = 4096
        r = self._get_request(**kwargs)
        if r.status_code != 200:
            print(f"Response obtained: {r.status_code}")
            return None

        print(r.content)
        buf = io.BytesIO(r.content)
        return Image.open(buf)

    def _put_request(self, endpoint, query_params=None):
        print(f"Requesting PUT on {endpoint}...")
        gui_before = datetime.now()
        query = self._get_common_query()
        if query_params is not None:
            query.update(query_params)
        r = requests.put(f"{self._camera_address}/{endpoint}", data=json.dumps(query))
        gui_after = datetime.now()
        print(f"...returned code {r.status_code}")
        if r.status_code == 200:
            print(f"Received 200!")
            timestamps = json.loads(r.headers['Timestamps'])
            print(f"Timestamps = {timestamps}")

            server_before = datetime.strptime(timestamps["before"], default_format)
            server_after = datetime.strptime(timestamps["after"], default_format)

            ms_bc = get_diff_ms(server_after, server_before)
            ms_total = get_diff_ms(gui_after, gui_before)
            print(f"server time={ms_bc}ms, total={ms_total}ms")
        return r

    def get_gain(self):
        return int(self._get_request("gain").json()["Value"][0])

    def get_temperature(self):
        return self._get_request("ccdtemperature").json()["Value"]

    def set_init(self):
        r = self._put_request("init")
        return r.status_code == 200

    def set_gain(self, value):
        self._put_request("gain", query_params={"Gain": value})

    def get_imagesize(self):
        """
        :return: array [HEIGHT, WIDTH]
        """
        numx = int(self._get_request("numx").json()["Value"])
        numy = int(self._get_request("numy").json()["Value"])
        return [numy, numx]

    def get_image_and_save_file(self):
        headers = {"Content-type": "application/octet-stream"}
        return self._get_request("saveimageandsendbytes", headers=headers)

    def get_camera_readout_modes(self):
        r = self._get_request("readoutmodes").json()
        print(r)
        return r["Value"]

    def get_exposure(self):
        return 0

    def get_current_readout_mode(self):
        return self._get_request("readoutmode").json()["Value"]

    def set_readout_mode(self, value):
        self._put_request("readoutmode", {"ReadoutMode": value})

    def is_alive(self):
        try:
            status_address = f"{self._address}status"
            r = requests.get(status_address)
            return r.json()["server"] == "OK"
        except Exception as e:
            print(f"Is alive failed: {repr(e)}")
            return False

    def get_camerastate(self):
        return self._get_request("camerastate")

    def put_startexposure(self, duration_s):
        return self._put_request("startexposure", {"Duration": duration_s, "Light": True, "Save": True}).json()

    def put_capture(self, duration_s, images_no):
        self._put_request("capture", query_params={"Number": images_no, "Duration": duration_s})

    def put_instant_capture(self, duration_s):
        res = self._put_request("instantcapture", query_params={"Light": True, "Duration": duration_s})
        return res.content

    def get_image_bytes(self):
        headers = {"Content-type": "application/octet-stream"}
        return self._get_request("imagebytes", headers=headers)

    def get_last_image(self):
        return self._get_image_from_stream(endpoint="lastimage")

    def get_image_array(self):
        return self._get_request("imagearray")

    def get_image_file(self, filename):
        return self._get_request("imagefile", {"Filename": filename})

    def is_image_ready(self):
        r = self._get_request("imageready").json()
        return r["Value"]

    def get_one_image(self, exposure_s, image_size):
        error_counter = 0
        error_allowed = 10  # TODO!!!! THIS MAY BE DANGEORUS!
        max_iter = 10
        # TODO!!!! above constants!
        image_size = image_size[0:2]
        print(f"Using image size: {image_size}")
        get_cs = self.get_camerastate().json()
        print(f"Get cs = {get_cs}")
        state = get_cs["Value"]
        str_state = ascom_states[state]
        if str_state == "IDLE" or (str_state == "ERROR" and error_counter < error_allowed):
            if str_state == "ERROR":
                error_counter += 1
            self.put_startexposure(exposure_s)
            time.sleep(exposure_s+0.3)
            iter_count = 1
            ready = self.is_image_ready()
            while not ready and iter_count < max_iter:
                time.sleep(0.5)
                iter_count += 1
                ready = self.is_image_ready()
            if not ready:
                return None
            return self.get_image_bytes().content
