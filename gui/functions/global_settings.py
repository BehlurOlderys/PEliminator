from math import cos, radians


arcseconds_per_2pi = 1296000.0
arcseconds_per_um = 206.264
us_in_1_second = 1000000.0
possible_units = ["steps", "arcsec", "pixels"]


mount_server_port = 50110


class GlobalSettings:

    # constants:
    sidereal_day_s = 86164
    arcsec_full_circle = 1296000
    sidereal_speed = arcsec_full_circle / sidereal_day_s

    def __init__(self):
        self._stepper_microstep_as = 0.6
        self._encoder_resolution_lpi = 200
        self._encoder_cpr = 1800
        self._error_threshold = 0.25
        self._error_gain = 1.5
        self._max_correction = 1
        self._arcsec_per_strip = GlobalSettings.arcsec_full_circle / self._encoder_cpr
        self._visualisation_on = True
        self._fragment_size = 70
        self._focal_length = 650
        self._pixel_pitch = 2.9
        self._declination_deg = 20.0
        self._correction_bins = 20
        self._worm_encoder_ticks = 4096
        self._worm_teeth = 130
        self._correction_direction = 'positive'
        self._encoder_history_size = 10000
        self._minimal_full_period_points = 18
        self._focal = 650
        self._pixel = 2.9
        self._averager_max = 48
        self._initial_scale_amendment = 0.00
        self._star_tracking_average = 5
        self._star_tracking_pipe_name = "logs//star_tracking_pipe"
        self._initial_feedback_gain = 0.005
        self._initial_dec_feedback_gain = 1
        self._frame_length_s = 30

    def get_stepper_microstep_as(self):
        return self._stepper_microstep_as

    def get_frame_length_s(self):
        return self._frame_length_s

    def set_frame_length_s(self):
        return self._frame_length_s

    def get_initial_feedback_gain(self):
        return self._initial_feedback_gain

    def get_initial_dec_feedback_gain(self):
        return self._initial_dec_feedback_gain

    def get_star_tracking_pipe_name(self):
        return self._star_tracking_pipe_name

    def get_star_tracking_average(self):
        return self._star_tracking_average

    def get_initial_scale_amendment(self):
        return self._initial_scale_amendment

    def get_averager_max(self):
        return self._averager_max

    def get_encoder_resolution_lpi(self):
        return self._encoder_resolution_lpi

    def get_encoder_cpr(self):
        return self._encoder_cpr

    def get_error_threshold(self):
        return self._error_threshold

    def get_error_gain(self):
        return self._error_gain

    def get_max_correction(self):
        return self._max_correction

    def get_arcsec_per_strip(self):
        return self._arcsec_per_strip

    def get_focal_length(self):
        return self._focal

    def get_pixel_pitch(self):
        return self._pixel

    def get_encoder_history_size(self):
        return self._encoder_history_size

    def get_worm_speed_factor(self):
        return arcseconds_per_2pi / self._worm_encoder_ticks

    def get_correction_direction(self):
        return self._correction_direction

    def get_worm_teeth(self):
        return self._worm_teeth

    def get_minimal_full_period_points(self):
        return self._minimal_full_period_points

    def get_encoder_ticks(self):
        return self._worm_encoder_ticks

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
