from datetime import datetime

from common.convert_currency import convert_currency
from common.convert_currency import get_currency_converter_intance


def test_convert_currency():
    converter = get_currency_converter_intance()
    assert round(convert_currency(converter, 10, "EUR", datetime(2022, 8, 20)), 2) == 10.04
    assert convert_currency(converter, 10, "USD", datetime(2022, 8, 20)) == 10
