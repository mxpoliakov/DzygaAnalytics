from datetime import datetime
from unittest.mock import patch

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
from common.mongo import write_df_to_collection_with_logs
from mongo.enforce_schema import enforce_schema


def test_connection_to_mongo():
    assert get_collection().name == get_collection_name()


@pytest.mark.parametrize("donation_source", get_sources_names_list())
def test_get_last_document_datetime(donation_source):
    last_document_datetime = get_last_document_datetime(donation_source)
    assert isinstance(last_document_datetime, datetime)


def test_get_last_document_datetime_fail():
    with pytest.raises(ValueError):
        get_last_document_datetime("Does not exist")


@patch("common.mongo.get_collection_name")
def test_write_df_to_collection(get_collection_name_mock, capsys):
    db = get_database()

    test_collection_name = f"test_donations_{ObjectId()}"
    get_collection_name_mock.return_value = test_collection_name
    db.create_collection(test_collection_name)
    enforce_schema(test_collection_name)

    df = pd.read_csv("tests/test_data/sample.csv", parse_dates=["Datetime"])
    df["Note"] = df["Note"].fillna("")
    df = df.where(pd.notnull(df), None)

    sources = get_sources_names_list()
    for source in get_sources_names_list():
        write_df_to_collection_with_logs(
            df,
            start_datetime="1",
            end_datetime="2",
            donation_source=source,
        )
        assert f"1 - 2 | {source} | Wrote {len(df)} rows" in capsys.readouterr().out

    write_df_to_collection_with_logs(pd.DataFrame({}), start_datetime="1", end_datetime="2")
    assert "1 - 2 | PayPal | No data" in capsys.readouterr().out

    with pytest.raises(BulkWriteError, match="donationSource"):
        write_df_to_collection(df, donation_source="Not Allowed")

    enforce_schema(test_collection_name, sources=sources + ["Not Allowed"])

    write_df_to_collection(df, donation_source="Not Allowed")

    db.drop_collection(test_collection_name)
