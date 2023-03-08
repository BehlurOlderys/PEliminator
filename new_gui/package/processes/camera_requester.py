import requests
import json
import time
import numpy as np
from PIL import Image
import io
from package.ascom.ascom_camera import CameraState


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

    def _get_common_query(self):
        return {"ClientID": self._cid, "ClientTransactionID": self._rc.get_new_count()}


class CameraRequests(AscomRequests):
    def __init__(self, camera_no, **kwargs):
        super(CameraRequests, self).__init__(**kwargs)
        self._address += f"camera/{camera_no}"

    def _get_request(self, endpoint, query_params=None, headers=None, stream=False):
        print(f"GET request for {self._address}/{endpoint}...")
        headers = headers if headers else {}
        query = self._get_common_query()
        if query_params is not None:
            query.update(query_params)
        r = requests.get(f"{self._address}/{endpoint}", params=query, headers=headers, stream=stream)
        print(f"...returned code {r.status_code}")
        return r

    def _get_image_from_stream(self, **kwargs):
        CHUNK_SIZE = 4096
        r = self._get_request(**kwargs)
        if r.status_code != 200:
            print(f"Response obtained: {r.status_code}")
            return None

        buf = io.BytesIO(r.content)
        return Image.open(buf)

        # buf = io.BytesIO()
        # for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
        #     buf.write(chunk)
        #
        # buf.seek(0)
        # return Image.open(buf)

        with open("latest.tif", 'wb') as image_file:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                print(f"chunk!")
                image_file.write(chunk)
        print(f"Saved image!")

    def _put_request(self, endpoint, query_params=None):
            query = self._get_common_query()
            if query_params is not None:
                query.update(query_params)
            return requests.put(f"{self._address}/{endpoint}", data=json.dumps(query))

    def get_gain(self):
        return int(self._get_request("gain").json()["Value"][0])

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

    def get_camerastate(self):
        return self._get_request("camerastate").json()

    def put_startexposure(self, duration_s):
        return self._put_request("startexposure", {"Duration": duration_s, "Light": True, "Save": True}).json()

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

    def get_one_image(self, exposure_s, image_type, image_size):
        error_counter = 0
        error_allowed = 10  # TODO!!!! THIS MAY BE DANGEORUS!
        max_iter = 10
        # TODO!!!! above constants!
        image_size = image_size[0:2]
        print(f"Using image size: {image_size}")
        state = self.get_camerastate()["Value"]
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
            print(f"Image type = {image_type}")
            return self.get_image_bytes().content
