import os

from pymongo import DESCENDING
from pymongo import MongoClient
from pymongo.collection import Collection


def get_collection() -> Collection:
    connection = MongoClient(os.environ["MONGO_URI"])["AppDB"]
    return connection.get_collection("donations")


def write_df_to_collection_with_logs(
    df, last_document_datetime, current_datetime, donation_source="PayPal", insertion_mode="Manual"
):
    base_str = f"{last_document_datetime} - {current_datetime} | {donation_source} |"
    if not df.empty:
        write_df_to_collection(df, donation_source, insertion_mode)
        print(f"{base_str} Wrote {len(df)} rows")
    else:
        print(f"{base_str} | No data")


def write_df_to_collection(df, donation_source="PayPal", insertion_mode="Manual"):
    rows_to_insert = []
    for _, row in df.iterrows():
        row_insert = {
            "donationSource": donation_source,
            "senderName": row["Name"],
            "senderEmail": row["Email"],
            "currency": row["Currency"],
            "amountUSD": row["Converted Sum"],
            "amountOriginal": row["Original Sum"],
            "senderNote": row["Note"],
            "datetime": row["Datetime"].to_pydatetime(),
            "insertionMode": insertion_mode,
        }
        rows_to_insert.append(row_insert)

    get_collection().insert_many(rows_to_insert)


def get_last_document_datetime(donation_source, convert_to_str=True):
    last_document = get_collection().find_one(
        {"donationSource": donation_source}, sort=[("datetime", DESCENDING)]
    )
    if last_document is None:
        raise ValueError(f"No data is in the collection for source {donation_source}")

    if convert_to_str:
        return last_document["datetime"].strftime("%Y-%m-%dT%H:%M:%SZ")

    return last_document["datetime"]
