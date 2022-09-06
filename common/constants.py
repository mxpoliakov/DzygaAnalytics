"""This module contains constants for common use"""
from datetime import timedelta

DELTA_TIME_PERIOD = timedelta(days=25)

MONOBANK_ENDPOINT_URL = "https://api.monobank.ua"
PAYPAL_ENDPOINT_URL = "https://api-m.paypal.com/v1"

ALLOWED_PAYPAL_TRANSACTIONS_TYPES = ["T0000", "T0011"]
MAX_PAYPAL_TRANSACTIONS = 500

UAH_CODE = 980
USD_CODE = 840
DEFAULT_USD_UAH_CONVERTION_RATE = 40.0
