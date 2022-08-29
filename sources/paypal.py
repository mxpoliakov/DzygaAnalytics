import json
import os
from datetime import datetime

import pandas as pd
import requests

from common.config import get_creds_keys_list
from common.convert_currency import convert_currency
from common.convert_currency import get_currency_converter_intance
from sources.base import SourceBase

PAYPAL_ENDPOINT_URL = "https://api-m.paypal.com/v1"
MAX_PAYPAL_TRANSACTIONS = 500


class PayPal(SourceBase):
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

        # Skip first transaction returned, because it is already stored in the database.
        return response["transaction_details"][1:]

    def get_api_data(self, start_datetime: datetime, end_datetime: datetime) -> pd.DataFrame:
        transactions = self.get_api_data_raw(start_datetime, end_datetime)
        rows = []

        currency_converter_intance = get_currency_converter_intance()

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
                        "Converted Sum": convert_currency(
                            currency_converter_intance, net, currency, transaction_dt
                        ),
                        "Original Sum": net,
                        "Currency": currency,
                        "Datetime": transaction_dt,
                        "Note": transaction_info.get("transaction_note", ""),
                    }
                )
        df = pd.DataFrame.from_dict(rows)
        return df
