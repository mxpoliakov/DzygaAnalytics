"""This module contains class for Monobank donation source"""
from datetime import datetime

import pandas as pd

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
        start_datetime = int(self.start_datetime.timestamp())
        end_datetime = int(self.end_datetime.timestamp())
        url = (
            f"{MONOBANK_ENDPOINT_URL}/personal/statement/{account_id}/"
            f"{start_datetime}/{end_datetime}"
        )
        headers = {
            "Content-Type": "application/json",
            "X-Token": self.source_config["x_token"],
        }
        response = self.get_request_with_rate_limiting(url, headers)

        rows = []

        transactions = response[::-1]  # Reverse list

        for transaction in transactions:
            if not self.is_source_creation_date and transaction["time"] == start_datetime:
                # Skip transaction with the same time as start_datetime,
                # because it is already stored in the database.
                continue

            # Transaction amount is encoded as int with decimals
            amount = transaction["amount"] / 100
            if amount > 0:
                try:
                    name = transaction["description"].split("Від: ")[1]
                except IndexError:
                    name = "🐈"

                sender_note = transaction.get("comment", "")
                rows.append(
                    {
                        "senderName": name if name != "🐈" else None,
                        "senderEmail": self.parse_email_from_note(sender_note),
                        "amountOriginal": amount,
                        "currency": self.source_config["currency"],
                        "datetime": datetime.utcfromtimestamp(transaction["time"]),
                        "senderNote": sender_note,
                        "countryCode": None,
                    }
                )

        df = pd.DataFrame.from_dict(rows)
        return df
