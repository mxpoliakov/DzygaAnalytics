"""This module contains tests for Monobank donation source"""
from datetime import datetime
from unittest.mock import Mock
from unittest.mock import patch

import pandas as pd
from bson import ObjectId

from common.mongo import get_database
from sources.monobank import Monobank


@patch("sources.base.datetime")
@patch("common.mongo.get_collection_name")
def test_write_new_data(get_collection_name_mock: Mock, datetime_mock: Mock) -> None:
    """This is an E2E test for Monobank source. The test creates fake collection
    in the database, and mocks start and end date to write PayPal transactions
    from real account between 2022-07-01 to 2022-08-01.

    Parameters
    ----------
    get_collection_name_mock : Mock
        A mock to swap collection name from config names to the test one.
    datetime_mock : Mock
        A mock to fake current datetime.
    """
    datetime_mock.utcnow = Mock(return_value=datetime(2022, 8, 1))
    datetime_mock.fromisoformat = datetime.fromisoformat
    test_collection_name = f"test_donations_{ObjectId()}"
    get_collection_name_mock.return_value = test_collection_name
    db = get_database()
    db.create_collection(test_collection_name)
    monobank = Monobank("Dzyga's Paw Jar")
    monobank.write_new_data()
    entries = list(db.get_collection(test_collection_name).find({}))
    df = pd.DataFrame.from_dict(entries)
    assert len(df) == 3
    assert df["amountOriginal"].sum() == 7500
    db.drop_collection(test_collection_name)
