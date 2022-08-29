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
from sources.paypal import PayPal


@pytest.mark.parametrize("creds_key", get_creds_keys_list("PayPal"))
def test_get_access_token(creds_key):
    paypal = PayPal(creds_key, "PayPal")
    assert isinstance(paypal.get_access_token(), str)


def test_get_api_data_does_not_include_payments_between_accounts():
    creds_key = get_sources()[1]["creds_key"]
    paypal = PayPal(creds_key, "PayPal")
    df = paypal.get_api_data(datetime(2022, 8, 22), datetime(2022, 8, 28))
    assert len(df) == 1
    assert df["Converted Sum"][0] == 50.0


@patch("sources.base.datetime")
@patch("sources.base.get_last_document_datetime")
@patch("common.mongo.get_collection_name")
def test_write_new_data(get_collection_name_mock, get_last_document_datetime_mock, datetime_mock):
    datetime_mock.utcnow = Mock(return_value=datetime(2022, 8, 2))
    datetime_mock.fromisoformat = datetime.fromisoformat
    get_last_document_datetime_mock.return_value = datetime(2022, 8, 1)
    test_collection_name = f"test_donations_{ObjectId()}"
    get_collection_name_mock.return_value = test_collection_name
    db = get_database()
    db.create_collection(test_collection_name)
    enforce_schema(test_collection_name)
    source = get_sources()[0]
    paypal = PayPal(creds_key=source["creds_key"], donation_source=source["name"])
    paypal.write_new_data()
    entries = list(db.get_collection(test_collection_name).find({}))
    df = pd.DataFrame.from_dict(entries)
    assert len(df) == 4
    assert df["senderNameCensored"][0] == "St**** JP"
    assert df["amountUSD"].sum() == 250.64
    assert df["donationSource"].unique()[0] == source["name"]
    assert df["insertionMode"].unique()[0] == "Auto"
    db.drop_collection(test_collection_name)
