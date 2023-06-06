import numpy as np
from PIL import Image
from astropy.io import fits


def get_np_array_from_fits(filepath):
    hdul = fits.open(filepath)
    image_data = hdul[0].data
    return image_data


def get_np_array_from_png(filepath):
    im_frame = Image.open(filepath)
    return np.array(im_frame)


image_openers_map = {
    "fits": get_np_array_from_fits,
    "png": get_np_array_from_png
}
