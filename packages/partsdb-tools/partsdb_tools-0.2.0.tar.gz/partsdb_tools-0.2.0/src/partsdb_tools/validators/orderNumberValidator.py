from ..common import load_packaging_types

order_number_allowed_fields = [
    '12NC',
    'EAN13',
    'SKU',
    'alias',
    'status',
    'code',
    'type',
    'qty',
    'packagingData']

def validate_order_number_fields(part):
    for order_number in part['orderNumbers']:
        order = part['orderNumbers'][order_number]
        for field in order:
            if field not in order_number_allowed_fields:
                return False

        if not validate_packaging_type(order):
            return False
    return True


def validate_packaging_type(order_number):
    if 'type' in order_number:
        if order_number['type'] not in load_packaging_types():
            return False
    return True

