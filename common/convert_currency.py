from currency_converter import ECB_URL
from currency_converter import CurrencyConverter

currency_converter_intance = None


def convert_currency(value, currency, date):
    global currency_converter_intance
    currency_converter_intance = (
        CurrencyConverter(ECB_URL, fallback_on_missing_rate=True, fallback_on_wrong_date=True)
        if currency_converter_intance is None
        else currency_converter_intance
    )

    if currency != "USD":
        return currency_converter_intance.convert(value, currency, "USD", date=date)
    else:
        return value
