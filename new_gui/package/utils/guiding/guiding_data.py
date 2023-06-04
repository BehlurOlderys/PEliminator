
class GuidingData:
    def __init__(self, im, t, shname):
        self.image = im
        self.timestamp = t
        self.shortname = shname
        self.start = None
        self.message = "OK"
        self.error = False
        self.fragment = None
        self.fragment_rect = None
        self.calculated_center = None

    def __repr__(self):
        return self.message
