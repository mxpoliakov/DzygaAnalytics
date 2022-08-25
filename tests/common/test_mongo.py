from datetime import datetime

import pandas as pd
import pytest
from bson import ObjectId
from pymongo.errors import BulkWriteError

from common.config import get_collection_name
from common.config import get_sources_names_list
from common.mongo import get_collection
from common.mongo import get_database
from common.mongo import get_last_document_datetime
from common.mongo import write_df_to_collection
from mongo.enforce_schema import enforce_schema


def test_connection_to_mongo():
    assert get_collection().name == get_collection_name()


@pytest.mark.parametrize("convert_to_str", [True, False])
@pytest.mark.parametrize("donation_source", get_sources_names_list())
def test_get_last_document_datetime(convert_to_str, donation_source):
    last_document_datetime = get_last_document_datetime(donation_source, convert_to_str)
    assert isinstance(last_document_datetime, str if convert_to_str else datetime)


def test_write_df_to_collection():
    db = get_database()

    test_collection_name = f"test_donations_{ObjectId()}"
    db.create_collection(test_collection_name)
    enforce_schema(test_collection_name)

    df = pd.read_csv("tests/test_data/sample.csv", parse_dates=["Datetime"])
    df["Note"] = df["Note"].fillna("")
    df = df.where(pd.notnull(df), None)

    sources = get_sources_names_list()
    for source in get_sources_names_list():
        write_df_to_collection(df, test_collection_name, donation_source=source)

    with pytest.raises(BulkWriteError, match="donationSource"):
        write_df_to_collection(df, test_collection_name, donation_source="Not Allowed")

    enforce_schema(test_collection_name, sources=sources + ["Not Allowed"])

    write_df_to_collection(df, test_collection_name, donation_source="Not Allowed")

    db.drop_collection(test_collection_name)
