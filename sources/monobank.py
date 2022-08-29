import json
import os
from datetime import datetime

import pandas as pd
import requests

from sources.base import SourceBase

MONOBANK_ENDPOINT_URL = "https://api.monobank.ua"
UAH_CODE = 980
USD_CODE = 840
DEFAULT_CONVERTION_RATE = 40


class Monobank(SourceBase):
    def get_usd_to_uah_current_rate(self) -> float:
        response = requests.get(
            f"{MONOBANK_ENDPOINT_URL}/bank/currency",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == requests.codes["ok"], response.text
        response = json.loads(response.text)

        for rate_info in response:
            if rate_info["currencyCodeA"] == USD_CODE and rate_info["currencyCodeB"] == UAH_CODE:
                return rate_info["rateSell"]
        return DEFAULT_CONVERTION_RATE

    def get_api_data(self, start_datetime: datetime, end_datetime: datetime) -> pd.DataFrame:
        account_id = os.environ[f"{self.creds_key}_ACCOUNT_ID"]
        url = (
            f"{MONOBANK_ENDPOINT_URL}/personal/statement/"
            f"{account_id}/{int(start_datetime.timestamp())}/{int(end_datetime.timestamp())}"
        )
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "X-Token": os.environ[f"{self.creds_key}_X_TOKEN"],
            },
        )
        assert response.status_code == requests.codes["ok"], response.text
        response = json.loads(response.text)

        rows = []
        rate = self.get_usd_to_uah_current_rate()
        transactions = response[::-1]  # Reverse list
        if not self.is_start_datetime_creation_date(start_datetime):
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

                assert transaction["currencyCode"] == UAH_CODE, "Only UAH accounts are supported"
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
