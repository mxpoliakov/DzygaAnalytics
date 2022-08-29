import json
import os
from datetime import datetime

import pandas as pd
import requests
from currency_converter import ECB_URL
from currency_converter import CurrencyConverter

from common.config import get_creds_keys_list
from sources.base import SourceBase

PAYPAL_ENDPOINT_URL = "https://api-m.paypal.com/v1"
MAX_PAYPAL_TRANSACTIONS = 500


class PayPal(SourceBase):
    def __init__(self, creds_key: str, donation_source: str):
        super().__init__(creds_key, donation_source)
        self.currency_converter = CurrencyConverter(
            ECB_URL, fallback_on_missing_rate=True, fallback_on_wrong_date=True
        )

    def convert_currency(self, value: float, currency: str, date: datetime) -> float:
        if currency != "USD":
            return self.currency_converter.convert(value, currency, "USD", date=date)
        return value

    def get_access_token(self) -> str:
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

    def get_api_data_raw(self, start_datetime: datetime, end_datetime: datetime) -> dict:
        access_token = self.get_access_token()
        response = requests.get(
            f"{PAYPAL_ENDPOINT_URL}/reporting/transactions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
                "Accept-Language": "en_US",
            },
            params={
                "start_date": start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_date": end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "page_size": MAX_PAYPAL_TRANSACTIONS,
                "transaction_status": "S",
                "fields": ",".join(["transaction_info", "payer_info"]),
            },
        )
        assert response.status_code == requests.codes["ok"], response.text
        response = json.loads(response.text)

        if self.is_start_datetime_creation_date(start_datetime):
            return response["transaction_details"]

        # Skip first transaction returned, because it is already stored in the database.
        return response["transaction_details"][1:]

    def get_api_data(self, start_datetime: datetime, end_datetime: datetime) -> pd.DataFrame:
        transactions = self.get_api_data_raw(start_datetime, end_datetime)
        rows = []

        account_emails = [
            os.environ[f"{creds_key}_EMAIL"] for creds_key in get_creds_keys_list("PayPal")
        ]

        for transaction in transactions:
            transaction_info = transaction["transaction_info"]
            code = transaction_info["transaction_event_code"]
            net = float(transaction_info["transaction_amount"]["value"])
            if code in ["T0000", "T0011"] and net > 0:
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
                        "Name": payer_info["payer_name"]["alternate_full_name"],
                        "Email": payer_info["email_address"],
                        "Converted Sum": self.convert_currency(net, currency, transaction_dt),
                        "Original Sum": net,
                        "Currency": currency,
                        "Datetime": transaction_dt,
                        "Note": transaction_info.get("transaction_note", ""),
                    }
                )
        df = pd.DataFrame.from_dict(rows)
        return df
