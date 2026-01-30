class Box:
    def __init__(self, length, width, height, weight):
        self.length = length
        self.width = width
        self.height = height
        self.weight = weight

    def to_dict(self):
        result = {
            'l': self.length,
            'w': self.width,
            'h': self.height
        }
        if self.weight:
            result['weight'] = self.weight
        return result
