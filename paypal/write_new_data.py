import json
import os
from datetime import datetime

import pandas as pd
import requests

from common.convert_currency import convert_currency
from common.convert_currency import get_currency_converter_intance
from common.mongo import get_last_document_datetime
from common.mongo import write_df_to_collection_with_logs

PAYPAL_ENDPOINT_URL = "https://api-m.paypal.com/v1"
MAX_PAYPAL_TRANSACTIONS = 500


def get_access_token(creds_key):
    response = requests.post(
        f"{PAYPAL_ENDPOINT_URL}/oauth2/token",
        auth=(os.environ[f"{creds_key}_CLIENT_ID"], os.environ[f"{creds_key}_SECRET_ID"]),
        headers={"Accept": "application/json", "Accept-Language": "en_US"},
        data={"grant_type": "client_credentials"},
    ).json()

    return response["access_token"]


def get_paypal_api_data(access_token, last_document_datetime):
    current_datetime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    response = requests.get(
        f"{PAYPAL_ENDPOINT_URL}/reporting/transactions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Accept-Language": "en_US",
        },
        params={
            "start_date": last_document_datetime,
            "end_date": current_datetime,
            "page_size": MAX_PAYPAL_TRANSACTIONS,
            "transaction_status": "S",
            "fields": ",".join(["transaction_info", "payer_info"]),
        },
    )
    assert response.status_code == requests.codes["ok"], response.text
    response = json.loads(response.text)

    rows = []

    # Skip first transaction returned, because it is already stored in the database.
    transactions = response["transaction_details"][1:]

    currency_converter_intance = get_currency_converter_intance()

    for transaction in transactions:
        transaction_info = transaction["transaction_info"]
        code = transaction_info["transaction_event_code"]
        net = float(transaction_info["transaction_amount"]["value"])
        if code in ["T0000", "T0011"] and net > 0:
            payer_info = transaction["payer_info"]
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
    return df, current_datetime


def write_new_data(creds_key, donation_source="PayPal"):
    access_token = get_access_token(creds_key)
    last_document_datetime = get_last_document_datetime(donation_source)
    df, current_datetime = get_paypal_api_data(access_token, last_document_datetime)
    write_df_to_collection_with_logs(
        df, last_document_datetime, current_datetime, donation_source, "Auto"
    )
