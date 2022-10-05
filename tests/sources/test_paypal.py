"""This module contains tests for PayPal donation source"""
from datetime import datetime
from unittest.mock import Mock
from unittest.mock import patch

import pandas as pd
import pytest
from bson import ObjectId

from common.config import get_source
from common.mongo import get_database
from mongo.enforce_schema import enforce_schema
from sources.paypal import PayPal


@pytest.mark.parametrize("name", ["Dimko's PayPal", "Roman's PayPal"])
def test_get_access_token(name) -> None:
    """Tests if can get access token for all PayPal accounts specified in config file"""
    paypal = PayPal(name)
    assert isinstance(paypal.get_access_token(), str)


def test_get_api_data_does_not_include_payments_between_accounts() -> None:
    """Tests that we don't include cross account transaction between 2022-08-22 and 2022-08-28"""
    paypal = PayPal("Roman's PayPal")
    paypal.start_datetime = datetime(2022, 8, 22)
    paypal.end_datetime = datetime(2022, 8, 28)
    df = paypal.get_api_data()
    assert len(df) == 1
    assert df["amountOriginal"][0] == 50.0


@patch("sources.base.datetime")
@patch("sources.base.get_source")
@patch("common.mongo.get_collection_name")
def test_write_new_data(
    get_collection_name_mock: Mock, get_source_mock: Mock, datetime_mock: Mock
) -> None:
    """This is an E2E test for PayPal source. The test creates fake collection
    in the database, and mocks start and end date to write PayPal transactions
    from real account between 2022-08-01 to 2022-08-02.

    Parameters
    ----------
    get_collection_name_mock : Mock
        A mock to swap collection name from config names to the test one.
    get_source_mock : Mock
        A mock to swap account creation date from config names to the test one.
    datetime_mock : Mock
        A mock to fake current datetime.
    """
    datetime_mock.utcnow = Mock(return_value=datetime(2022, 8, 2))
    datetime_mock.fromisoformat = datetime.fromisoformat
    source = get_source("Dimko's PayPal")
    source["creation_date"] = datetime(2022, 8, 1)
    get_source_mock.return_value = source
    test_collection_name = f"test_donations_{ObjectId()}"
    get_collection_name_mock.return_value = test_collection_name
    db = get_database()
    db.create_collection(test_collection_name)
    enforce_schema(test_collection_name)
    paypal = PayPal(source["name"])
    paypal.is_source_creation_date = False
    paypal.write_new_data()
    entries = list(db.get_collection(test_collection_name).find({}))
    df = pd.DataFrame.from_dict(entries)
    assert len(df) == 4
    assert df["senderNameCensored"][0] == "St**** JP"
    assert df["countryCode"][0] == "US"
    assert df["amountUSD"].sum() == 250.64
    assert df["donationSource"].unique()[0] == source["name"]
    assert df["insertionMode"].unique()[0] == "Auto"
    db.drop_collection(test_collection_name)
