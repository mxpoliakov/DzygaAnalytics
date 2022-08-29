import os
from datetime import datetime

import pandas as pd
from pymongo import DESCENDING
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from common.config import get_collection_name
from common.config import get_db_name
from common.config import get_source


def get_database() -> Database:
    return MongoClient(os.environ["MONGO_URI"])[get_db_name()]


def get_collection(collection_name: None | str = None) -> Collection:
    collection_name = collection_name if collection_name is not None else get_collection_name()
    return get_database().get_collection(collection_name)


def write_df_to_collection_with_logs(
    df: pd.DataFrame,
    start_datetime: str | datetime,
    end_datetime: str | datetime,
    donation_source: str = "PayPal",
    insertion_mode: str = "Manual",
) -> None:
    base_str = f"{start_datetime} - {end_datetime} | {donation_source} |"
    if not df.empty:
        write_df_to_collection(df, donation_source, insertion_mode)
        print(f"{base_str} Wrote {len(df)} rows")
    else:
        print(f"{base_str} No data")


def mask_name(name: None | str, chars_to_keep: int = 2) -> str:
    if isinstance(name, str):
        return " ".join(
            [word[:chars_to_keep] + "*" * len(word[chars_to_keep:]) for word in name.split()]
        )
    return ""


def write_df_to_collection(
    df: pd.DataFrame, donation_source: str = "PayPal", insertion_mode: str = "Manual"
):
    rows_to_insert = []
    for _, row in df.iterrows():
        row_insert = {
            "donationSource": donation_source,
            "senderName": row["Name"],
            "senderNameCensored": mask_name(row["Name"]),
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


def get_last_document_datetime(donation_source: str) -> datetime:
    last_document = get_collection().find_one(
        {"donationSource": donation_source}, sort=[("datetime", DESCENDING)]
    )
    if last_document is None:
        return get_source(donation_source)["creation_date"]

    return last_document["datetime"]
