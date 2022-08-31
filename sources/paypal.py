"""This module contains class for PayPal donation source"""
import json
import os
from datetime import datetime

import pandas as pd
import requests
from currency_converter import ECB_URL
from currency_converter import CurrencyConverter
from currency_converter import ECB_URL
from currency_converter import CurrencyConverter

from common.config import get_creds_keys_list
from sources.base import SourceBase

PAYPAL_ENDPOINT_URL = "https://api-m.paypal.com/v1"
ALLOWED_TRANSACTIONS_TYPES = ["T0000", "T0011"]
MAX_PAYPAL_TRANSACTIONS = 500


class PayPal(SourceBase):
    """A class for retrieving PayPal API transactions.
    This supports personal PayPal accounts and can convert
    multiple currencies into USD using currency_converter package.

    We need following secret environment variables:
    {CREDS_KEY}_CLIENT_ID, {CREDS_KEY}_SECRET_ID and {CREDS_KEY}_EMAIL

    Parameters
    ----------
    creds_key : str
        The credential key for the source to access secret environment variables
    donation_source : str
        The donation source name
    """

    def __init__(self, creds_key: str, donation_source: str):
        super().__init__(creds_key, donation_source)
        self.currency_converter = CurrencyConverter(
            ECB_URL, fallback_on_missing_rate=True, fallback_on_wrong_date=True
        )

    def convert_currency(self, value: float, currency: str, date: datetime) -> float:
        """Convert currency into USD

        Parameters
        ----------
        value : float
            Transaction value
        currency : str
            Currency 3-letter code. For example, EUR
        date : datetime
            The transaction datetime

        Returns
        -------
        float
            Converted USD value
        """
        if currency != "USD":
            return self.currency_converter.convert(value, currency, "USD", date=date)
        return value

    def get_access_token(self) -> str:
        """Fetches a temp access token for PayPal API.
        More info: https://developer.paypal.com/api/rest/authentication/
        Two secret environment variables are required:
        {CREDS_KEY}_CLIENT_ID and {CREDS_KEY}_SECRET_ID

        Returns
        -------
        str
            Access token
        """
        response = requests.post(
            f"{PAYPAL_ENDPOINT_URL}/oauth2/token",
            auth=(
                os.environ[f"{self.creds_key}_CLIENT_ID"],
                os.environ[f"{self.creds_key}_SECRET_ID"],
            ),
            headers={"Accept": "application/json", "Accept-Language": "en_US"},
            data={"grant_type": "client_credentials"},
        ).json()

        return response["access_token"]

    def get_api_data_raw(self) -> dict:
        """Fetch raw data from PayPal transactions API. More info:
        https://developer.paypal.com/docs/api/transaction-search/v1/

        Returns
        -------
        dict
            Raw transactions data
        """
        access_token = self.get_access_token()
        response = requests.get(
            f"{PAYPAL_ENDPOINT_URL}/reporting/transactions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
                "Accept-Language": "en_US",
            },
            params={
                "start_date": self.start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_date": self.end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "page_size": MAX_PAYPAL_TRANSACTIONS,
                "transaction_status": "S",
                "fields": ",".join(["transaction_info", "payer_info"]),
            },
        )
        assert response.status_code == requests.codes["ok"], response.text
        response = json.loads(response.text)

        if self.is_source_creation_date:
            return response["transaction_details"]

        # Skip first transaction returned, because it is already stored in the database.
        return response["transaction_details"][1:]

    def get_api_data(self) -> pd.DataFrame:
        transactions = self.get_api_data_raw()
        rows = []

        account_emails = [
            os.environ[f"{creds_key}_EMAIL"] for creds_key in get_creds_keys_list("PayPal")
        ]

        for transaction in transactions:
            transaction_info = transaction["transaction_info"]
            code = transaction_info["transaction_event_code"]
            net = float(transaction_info["transaction_amount"]["value"])
            if code in ALLOWED_TRANSACTIONS_TYPES and net > 0:
                payer_info = transaction["payer_info"]
                if payer_info["email_address"] in account_emails:
                    # Avoid including payments between our PayPal accounts
                    continue
                currency = transaction_info["transaction_amount"]["currency_code"]
                transaction_dt = datetime.fromisoformat(
                    transaction_info["transaction_initiation_date"].split("+")[0]
                )
                rows.append(
                    {
                        "senderName": payer_info["payer_name"]["alternate_full_name"],
                        "senderEmail": payer_info["email_address"],
                        "amountUSD": self.convert_currency(net, currency, transaction_dt),
                        "amountOriginal": net,
                        "currency": currency,
                        "datetime": transaction_dt,
                        "senderNote": transaction_info.get("transaction_note", ""),
                    }
                )
        df = pd.DataFrame.from_dict(rows)
        return df
