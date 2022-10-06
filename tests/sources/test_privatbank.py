"""This module contains tests for Privatbank donation source"""
from datetime import datetime
from unittest.mock import Mock
from unittest.mock import patch

import pandas as pd
from bson import ObjectId

from common.config import get_source
from common.mongo import get_database
from sources.privatbank import Privatbank


@patch("sources.base.datetime")
@patch("sources.base.get_source")
@patch("common.mongo.get_collection_name")
def test_write_new_data(
    get_collection_name_mock: Mock, get_source_mock: Mock, datetime_mock: Mock
) -> None:
    """This is an E2E test for Privatbank source. The test creates fake collection
    in the database, and mocks start and end date to write Privatbank transactions
    from real account between 2022-09-01 to 2022-09-30.

    Parameters
    ----------
    get_collection_name_mock : Mock
        A mock to swap collection name from config names to the test one.
    get_source_mock : Mock
        A mock to swap account creation date from config names to the test one.
    datetime_mock : Mock
        A mock to fake current datetime.
    """
    datetime_mock.utcnow = Mock(return_value=datetime(2022, 9, 30))
    datetime_mock.fromisoformat = datetime.fromisoformat
    source = get_source("Dzyga's Paw Charity Accounts")
    source["creation_date"] = datetime(2022, 9, 1)
    get_source_mock.return_value = source
    test_collection_name = f"test_donations_{ObjectId()}"
    db = get_database()
    db.create_collection(test_collection_name)
    get_collection_name_mock.return_value = test_collection_name
    privatbank = Privatbank(source["name"])
    privatbank.is_source_creation_date = False
    privatbank.write_new_data()
    entries = list(db.get_collection(test_collection_name).find({}))
    df = pd.DataFrame.from_dict(entries)
    assert len(df) == 49
    assert df["senderNameCensored"][0] == "AL******* WI********"
    assert df["amountUSD"][0] == 508.90
    assert df["donationSource"].unique()[0] == source["name"]
    assert df["insertionMode"].unique()[0] == "Auto"
    db.drop_collection(test_collection_name)
