import decimal
import json


class DecimalEncoder(json.JSONEncoder):
    """
    Encoder for serializing Decimal Objects to JSON.

    https://stackforgeeks.com/blog/python-json-serialize-a-decimal-object
    """

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)
