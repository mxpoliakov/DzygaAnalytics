from currency_converter import ECB_URL
from currency_converter import CurrencyConverter


def get_currency_converter_intance():
    return CurrencyConverter(ECB_URL, fallback_on_missing_rate=True, fallback_on_wrong_date=True)


def convert_currency(currency_converter_intance, value, currency, date):
    if currency != "USD":
        return currency_converter_intance.convert(value, currency, "USD", date=date)
    return value
