import pymongo
from pymongo import MongoClient

from common.get_creds import get_creds


def get_last_document_datetime(donation_source, convert_to_str=True):
    client = MongoClient(get_creds()["mongo"]["uri"])
    conn = client["AppDB"]
    last_document = conn.get_collection("donations").find_one(
        {"donationSource": donation_source}, sort=[("datetime", pymongo.DESCENDING)]
    )
    if last_document is None:
        raise ValueError(f"No data is in the collection for source {donation_source}")

    if convert_to_str:
        return last_document["datetime"].strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        return last_document["datetime"]
