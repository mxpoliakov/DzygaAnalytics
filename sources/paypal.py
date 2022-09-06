"""This module contains class for PayPal donation source"""
import json
from datetime import datetime

import pandas as pd
import requests

from common.config import get_sources
from common.constants import ALLOWED_PAYPAL_TRANSACTIONS_TYPES
from common.constants import MAX_PAYPAL_TRANSACTIONS
from common.constants import PAYPAL_ENDPOINT_URL
from sources.base import SourceBase


class PayPal(SourceBase):
    """A class for retrieving PayPal API transactions.
    This supports personal PayPal accounts and can convert
    multiple currencies into USD using currency_converter package.

    We need following secret environment variables: CLIENT_ID and SECRET_ID

    Parameters
    ----------
    donation_source : str
        The donation source name
    """

    def get_access_token(self) -> str:
        """Fetches a temp access token for PayPal API.
        More info: https://developer.paypal.com/api/rest/authentication/
        Two secret environment variables are required: CLIENT_ID and SECRET_ID

        Returns
        -------
        str
            Access token
        """
        response = requests.post(
            f"{PAYPAL_ENDPOINT_URL}/oauth2/token",
            auth=(
                self.source_config["client_id"],
                self.source_config["secret_id"],
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

        account_emails = [source["email"] for source in get_sources("PayPal")]

        for transaction in transactions:
            transaction_info = transaction["transaction_info"]
            code = transaction_info["transaction_event_code"]
            net = float(transaction_info["transaction_amount"]["value"])
            if code in ALLOWED_PAYPAL_TRANSACTIONS_TYPES and net > 0:
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
                        "amountOriginal": net,
                        "currency": currency,
                        "datetime": transaction_dt,
                        "senderNote": transaction_info.get("transaction_note", ""),
                    }
                )
        df = pd.DataFrame.from_dict(rows)
        return df
