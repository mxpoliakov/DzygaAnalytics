from datetime import datetime
from unittest.mock import Mock
from unittest.mock import patch

import pandas as pd
from bson import ObjectId

from common.config import get_creds_keys_list
from common.mongo import get_database
from sources.monobank import Monobank


@patch("sources.base.datetime")
@patch("common.mongo.get_collection_name")
def test_write_new_data(get_collection_name_mock, datetime_mock):
    datetime_mock.utcnow = Mock(return_value=datetime(2022, 8, 1))
    datetime_mock.fromisoformat = datetime.fromisoformat
    test_collection_name = f"test_donations_{ObjectId()}"
    get_collection_name_mock.return_value = test_collection_name
    db = get_database()
    db.create_collection(test_collection_name)
    creds_key = get_creds_keys_list("Monobank").pop()
    paypal = Monobank(creds_key, donation_source="Dzyga's Paw Jar")
    paypal.write_new_data()
    entries = list(db.get_collection(test_collection_name).find({}))
    df = pd.DataFrame.from_dict(entries)
    assert len(df) == 3
    assert df["amountOriginal"].sum() == 7500
    db.drop_collection(test_collection_name)
