class Averager:
    def __init__(self):
        self.average_ratio = 0
        self.average_size = 0
        self.ratios = []

    def update_average(self, added):
        self.average_ratio = (self.average_size * self.average_ratio + added) / (self.average_size + 1)
        self.average_size += 1
        self.ratios.append(added)
        if len(self.ratios) > 1000:
            removed = self.ratios.pop(0)
            self.average_ratio = (self.average_size * self.average_ratio - removed) / (self.average_size - 1)
            self.average_size -= 1

        return self.average_ratio, self.average_size


averager = Averager()
