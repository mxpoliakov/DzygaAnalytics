import json
from datetime import datetime

import requests
import pandas as pd

from common.get_creds import get_creds

MONOBANK_ENDPOINT_URL = "https://api.monobank.ua"


def get_access_token_and_account_id(creds_key):
    monobank_creds = get_creds()[creds_key]
    return monobank_creds["x_token"], monobank_creds["account_id"]


def get_usd_to_uah_current_rate():
    response = requests.get(
        f"{MONOBANK_ENDPOINT_URL}/bank/currency",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200, response.text
    response = json.loads(response.text)

    for rate_info in response:
        if rate_info["currencyCodeA"] == 840 and rate_info["currencyCodeB"] == 980:
            return rate_info["rateSell"]
    return None


def get_monobank_api_data(access_token, account_id, start_datetime, end_datetime=None):
    start_datetime = int(start_datetime.timestamp())
    url = f"{MONOBANK_ENDPOINT_URL}/personal/statement/{account_id}/{start_datetime}"
    if end_datetime:
        end_datetime = int(end_datetime.timestamp())
        url += f"/{end_datetime}"
    response = requests.get(
        url,
        headers={"Content-Type": "application/json", "X-Token": access_token},
    )
    assert response.status_code == 200, response.text
    response = json.loads(response.text)

    rows = []
    rate = get_usd_to_uah_current_rate()
    transactions = response[::-1]  # Reverse list
    if not end_datetime:
        # If end_datetime, we already have some database entries.
        # Skip first transaction returned, because it is already stored in the database.
        transactions = transactions[1:]

    for transaction in transactions:
        amount = transaction["amount"] / 100
        converted_amount = round(amount / rate, 2)
        if converted_amount > 0:
            try:
                name = transaction["description"].split("Від: ")[1]
            except IndexError:
                name = "🐈"

            amount = transaction["amount"] / 100
            assert transaction["currencyCode"] == 980, "Only UAH accounts are supported"
            rows.append(
                {
                    "Name": name if name != "🐈" else None,
                    "Email": None,
                    "Converted Sum": converted_amount,
                    "Original Sum": amount,
                    "Currency": "UAH",
                    "Datetime": datetime.utcfromtimestamp(transaction["time"]),
                    "Note": transaction.get("comment", ""),
                }
            )

    df = pd.DataFrame.from_dict(rows)
    return df
