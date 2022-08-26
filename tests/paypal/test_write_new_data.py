from datetime import datetime
from unittest.mock import Mock
from unittest.mock import patch

import pandas as pd
import pytest
from bson import ObjectId

from common.config import get_creds_keys_list
from common.config import get_sources
from common.mongo import get_database
from mongo.enforce_schema import enforce_schema
from paypal.write_new_data import get_access_token
from paypal.write_new_data import write_new_data


@pytest.mark.parametrize("creds_key", get_creds_keys_list("PayPal"))
def test_get_access_token(creds_key):
    assert isinstance(get_access_token(creds_key), str)


@patch("paypal.write_new_data.datetime")
@patch("paypal.write_new_data.get_last_document_datetime")
@patch("common.mongo.get_collection_name")
def test_write_new_data(get_collection_name_mock, get_last_document_datetime_mock, datetime_mock):
    datetime_mock.utcnow = Mock(return_value=datetime(2022, 8, 2))
    datetime_mock.fromisoformat = datetime.fromisoformat
    get_last_document_datetime_mock.return_value = datetime(2022, 8, 1).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    test_collection_name = f"test_donations_{ObjectId()}"
    get_collection_name_mock.return_value = test_collection_name
    db = get_database()
    db.create_collection(test_collection_name)
    enforce_schema(test_collection_name)
    source = get_sources()[0]
    write_new_data(creds_key=source["creds_key"], donation_source=source["name"])
    entries = list(db.get_collection(test_collection_name).find({}))
    df = pd.DataFrame.from_dict(entries)
    assert len(df) == 4
    assert df["amountUSD"].sum() == 250.64
    assert df["donationSource"].unique()[0] == source["name"]
    assert df["insertionMode"].unique()[0] == "Auto"
    db.drop_collection(test_collection_name)
