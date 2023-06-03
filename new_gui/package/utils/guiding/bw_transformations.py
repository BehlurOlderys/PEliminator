from package.utils.guiding.data_processor import DataProcessor
import time
import numpy as np
import colour_demosaicing
import logging
log = logging.getLogger("guiding")


def rgb2gray(rgb):
    return np.dot(rgb[..., :3], [0.25, 0.5, 0.25])


def get_mono_normalized_from_color_raw_gbrg(data):
    st = time.time()
    float01_data = data.astype(np.float32) / 65535
    result = colour_demosaicing.demosaicing_CFA_Bayer_bilinear(float01_data, pattern="GBRG")
    bw_result = rgb2gray(result)
    en = time.time()
    log.debug(f"RAW transform took {1000*(en-st)}ms")
    return bw_result


raw_transforming_map = {
    "COLOR_RAW16_GBRG": get_mono_normalized_from_color_raw_gbrg
}


class NormalizedBWChanger(DataProcessor):
    def __init__(self, color: str, imtype: str, pattern: str = ""):
        super(NormalizedBWChanger, self).__init__("NormalizedBWChanger")
        designation = '_'.join([color, imtype, pattern])
        self._opening_mode = raw_transforming_map[designation]

    def _process_impl(self, data):
        data.image = self._opening_mode(data.image)
        return data