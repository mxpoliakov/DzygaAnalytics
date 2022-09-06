"""This module contains class for Monobank donation source"""
import json
from datetime import datetime

import pandas as pd
import requests

from common.constants import MONOBANK_ENDPOINT_URL
from sources.base import SourceBase


class Monobank(SourceBase):
    """A class for retrieving Monobank API transactions.
    API info in Ukrainian: https://api.monobank.ua/docs/

    We need following secret environment variables: ACCOUNT_ID and X_TOKEN

    Parameters
    ----------
    donation_source : str
        The donation source name
    """

    def get_api_data(self) -> pd.DataFrame:
        account_id = self.source_config["account_id"]
        url = (
            f"{MONOBANK_ENDPOINT_URL}/personal/statement/{account_id}/"
            f"{int(self.start_datetime.timestamp())}/{int(self.end_datetime.timestamp())}"
        )
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "X-Token": self.source_config["x_token"],
            },
        )
        assert response.status_code == requests.codes["ok"], response.text
        response = json.loads(response.text)

        rows = []

        transactions = response[::-1]  # Reverse list
        if not self.is_source_creation_date:
            # Skip first transaction returned, because it is already stored in the database.
            transactions = transactions[1:]

        for transaction in transactions:
            # Transaction amount is encoded as int with decimals
            amount = transaction["amount"] / 100
            if amount > 0:
                try:
                    name = transaction["description"].split("Від: ")[1]
                except IndexError:
                    name = "🐈"

                rows.append(
                    {
                        "senderName": name if name != "🐈" else None,
                        "senderEmail": None,
                        "amountOriginal": amount,
                        "currency": self.source_config["currency"],
                        "datetime": datetime.utcfromtimestamp(transaction["time"]),
                        "senderNote": transaction.get("comment", ""),
                    }
                )

        df = pd.DataFrame.from_dict(rows)
        return df
