import argparse
import json
from datetime import datetime

import pandas as pd
import requests

from common.convert_currency import convert_currency
from common.get_creds import get_creds
from common.get_last_document_datetime import get_last_document_datetime
from common.write_df_to_collection import write_df_to_collection

PAYPAL_ENDPOINT_URL = "https://api-m.paypal.com/v1"


def get_access_token(creds_key):
    paypal_creds = get_creds()[creds_key]
    response = requests.post(
        f"{PAYPAL_ENDPOINT_URL}/oauth2/token",
        auth=(paypal_creds["client_id"], paypal_creds["client_secret"]),
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
            "page_size": 500,
            "transaction_status": "S",
            "fields": ",".join(["transaction_info", "payer_info"]),
        },
    )
    assert response.status_code == 200, response.text
    response = json.loads(response.text)

    rows = []

    # Skip first transaction returned, because it is already stored in the database.
    transactions = response["transaction_details"][1:]

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
                    "Converted Sum": convert_currency(net, currency, transaction_dt),
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
    if not df.empty:
        write_df_to_collection(df, donation_source, "Auto")
        print(
            f"{last_document_datetime} - {current_datetime} | {donation_source} | Wrote {len(df)} rows"
        )
    else:
        print(f"{last_document_datetime} - {current_datetime} | {donation_source} | No data")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--creds_key", type=str, required=True)
    parser.add_argument("-d", "--donation_source", type=str, default="PayPal", required=False)
    args = parser.parse_args()
    write_new_data(args.creds_key, args.donation_source)
