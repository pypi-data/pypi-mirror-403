class Reel:
    def __init__(self, diameter, width=None):
        self.diameter = diameter
        self.width = width

    def to_dict(self):
        result = {
            'diameter': self.diameter
        }
        if self.width:
            result['width'] = self.width
        return result