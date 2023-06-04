from .data_processor import DataProcessor
from .guiding_data import GuidingData
from scipy.ndimage import gaussian_filter, median_filter, center_of_mass
import numpy as np
import logging
log = logging.getLogger("guiding")


def normalize(p):
    a = np.percentile(p, 5)
    b = np.percentile(p, 95)
    return (p - a) / (b-a)


class StarCenterCalculator(DataProcessor):
    def __init__(self):
        super(StarCenterCalculator, self).__init__("StarCenterCalculator")

    def _process_impl(self, data: GuidingData):
        if data.fragment is None:
            log.warning("Star center calculator received None")
            return data
        # fragment coordinates:
        tx, ty, h = data.fragment_rect

        # Preprocess image:
        image = gaussian_filter(median_filter(normalize(data.fragment), 5), 3)

        # Brightest pixel in coordinates of fragment:
        f_y, f_x = np.unravel_index(image.argmax(), image.shape)
        log.debug(f"Calculated star center in fragment as: ({f_x, f_y})")

        # Refine it with center of mass in smaller fragment around brightest pixel:
        narrowed_w = int(h // 3)
        #TODO while in narrow coordinates calculate CoM and go back to

        nx = f_x - narrowed_w//2
        ny = f_y - narrowed_w//2
        nfragment = image[ny:ny+narrowed_w, nx:nx+narrowed_w]
        cmy, cmx = center_of_mass(nfragment)
        log.debug(f"Refined star center in narrow fragment as: ({cmy, cmx})")

        # narrow_x0 = int(x0+mid_x-(narrowed_w//2))
        # narrow_y0 = int(y0+mid_y-(narrowed_w//2))
        # narrowed_fragment = image[narrow_y0:narrow_y0+narrowed_w, narrow_x0:narrow_x0+narrowed_w]
        # print(f"w = {w}, narrow_coords = ({narrow_x0},{narrow_y0}), Narrowed shape = {narrowed_fragment.shape}")

        # Refined coordinates are starting from nx-ys in real image
        f_x_refined = cmx + nx
        f_y_refined = cmy + ny
        log.debug(f"Refined star center in fragment as: ({f_x_refined, f_y_refined})")

        # final transform from fragment into whole image coordinates:
        real_x = f_x_refined + tx
        real_y = f_y_refined + ty
        data.calculated_center = real_x, real_y
        log.debug(f"Calculated star center in image as: ({real_x, real_y})")
        return data
