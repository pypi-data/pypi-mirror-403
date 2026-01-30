from decimal import Decimal
from .Box import Box


class BoxPackaging:
    def __init__(self, code, qty: int | Decimal, box: Box):
        self.code = code
        self.qty = qty
        self.box = box

    def to_dict(self):
        result = {
            'type': "Box",
            'code': self.code,
            'qty': self.qty
        }
        if self.box and self.box.to_dict():
            result['packagingData'] = {}
            result['packagingData']['box'] = self.box.to_dict()
        return result
