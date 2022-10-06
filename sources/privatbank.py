"""This module contains class for Privatbank donation source"""
import json
from datetime import datetime

import pandas as pd
import requests

from common.constants import MAX_PRIVATBANK_TRANSACTIONS
from common.constants import PRIVATBANK_ENDPOINT_URL
from sources.base import SourceBase


class Privatbank(SourceBase):
    """A class for retrieving Privatbank API transactions.
    This supports corporate Privatbank accounts of all currencies.
    We need following secret environment variables: TOKEN.

    Parameters
    ----------
    donation_source : str
        The donation source name
    """

    def get_api_data(self) -> pd.DataFrame:
        response = requests.get(
            f"{PRIVATBANK_ENDPOINT_URL}/statements/transactions",
            headers={
                "Content-Type": "application/json",
                "token": self.source_config["token"],
            },
            params={
                "startDate": self.start_datetime.strftime("%d-%m-%Y"),
                "limit": MAX_PRIVATBANK_TRANSACTIONS,
            },
        )
        assert response.status_code == requests.codes["ok"], response.text
        response = json.loads(response.text)
        transactions = response["transactions"]
        rows = []
        for transaction in transactions:
            sender_note = transaction["OSND"]
            if transaction["TRANTYPE"] == "C" and "Гривнi вiд продажу" not in sender_note:
                trasaction_datetime = datetime.strptime(
                    transaction["DATE_TIME_DAT_OD_TIM_P"], "%d.%m.%Y %H:%M:%S"
                )
                if not self.is_source_creation_date and trasaction_datetime <= self.start_datetime:
                    # Skip transaction with the same time as start_datetime,
                    # because it is already stored in the database.
                    continue
                currency = transaction["CCY"]
                if currency == "UAH":
                    name = transaction["AUT_CNTR_NAM"]
                    name = name if "Транз.рах." not in name else None
                    country_code = "UA"
                else:
                    if sender_note.split()[0] != "From":
                        # SWIFT transaction are duplicated.
                        # One of them always has 'From' as the first word.
                        continue
                    name = " ".join(sender_note.split()[1:3]).replace("1/", "")
                    country_code = None
                rows.append(
                    {
                        "senderName": name,
                        "senderEmail": self.parse_email_from_note(sender_note),
                        "amountOriginal": float(transaction["SUM"]),
                        "currency": currency,
                        "datetime": trasaction_datetime,
                        "senderNote": sender_note,
                        "countryCode": country_code,
                    }
                )
        df = pd.DataFrame.from_dict(rows)
        return df
