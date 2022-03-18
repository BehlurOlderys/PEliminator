class Settings:
    def __init__(self):
        self._focal = 650
        self._pixel = 2.9

    def get_focal_length(self):
        return self._focal

    def get_pixel_pitch(self):
        return self._pixel


settings = Settings()

possible_units = ["steps", "arcsec", "pixels"]