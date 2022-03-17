from math import cos, radians


arcseconds_per_2pi = 1296000.0
arcseconds_per_um = 206.264
us_in_1_second = 1000000.0


class GlobalSettings:
    def __init__(self):
        self._visualisation_on = True
        self._fragment_size = 70
        self._focal_length = 650
        self._pixel_pitch = 2.9
        self._declination_deg = 20.0
        self._correction_bins = 20
        self._encoder_ticks = 4096
        self._worm_teeth = 130
        self._correction_direction = 'positive'

    def get_worm_speed_factor(self):
        return arcseconds_per_2pi / self._encoder_ticks

    def get_correction_direction(self):
        return self._correction_direction

    def get_worm_teeth(self):
        return self._worm_teeth

    def get_encoder_ticks(self):
        return self._encoder_ticks

    def get_correction_bins(self):
        return self._correction_bins

    def get_image_scale(self):
        return cos(radians(self._declination_deg)) * arcseconds_per_um * self._pixel_pitch / self._focal_length

    def is_visualisation(self):
        return self._visualisation_on

    def get_fragment_size(self):
        return self._fragment_size

    def toggle_visualisation(self):
        self._visualisation_on = not self._visualisation_on
        return self._visualisation_on


settings = GlobalSettings()
