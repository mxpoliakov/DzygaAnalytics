"""This module contains tests for Manual donation source"""
from datetime import datetime
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from bson import ObjectId
from pymongo.errors import BulkWriteError
from pytest import CaptureFixture

from common.config import get_sources_names_list
from common.mongo import get_database
from mongo.enforce_schema import enforce_schema
from sources.manual import Manual


@patch("common.mongo.get_collection_name")
def test_write_new_data(get_collection_name_mock: Mock, capsys: CaptureFixture) -> None:
    """This is an E2E test for Manual source. We test if we can write the data
    from a csv file to the collection.

    Parameters
    ----------
    get_collection_name_mock : Mock
        A mock to swap collection name from config names to the test one.
    capsys : CaptureFixture
        Used to check what we print to logs.
    """
    db = get_database()
    test_collection_name = f"test_donations_{ObjectId()}"
    get_collection_name_mock.return_value = test_collection_name
    db.create_collection(test_collection_name)
    enforce_schema(test_collection_name)

    sources = get_sources_names_list()
    for source in sources:
        manual = Manual("KEY", source, "tests/test_data/sample.csv")
        manual.write_new_data()
        assert f"None - None | {source} | Wrote 6 rows" in capsys.readouterr().out

    manual = Manual("KEY", sources[0], "tests/test_data/empty.csv")
    manual.write_new_data()
    assert f"None - None | {sources[0]} | No data" in capsys.readouterr().out

    with patch("sources.base.get_source", return_value={"creation_date": datetime(2022, 8, 1)}):
        with pytest.raises(BulkWriteError, match="donationSource"):
            manual = Manual("KEY", "Not Allowed", "tests/test_data/sample.csv")
            manual.write_new_data()

        enforce_schema(test_collection_name, sources=sources + ["Not Allowed"])
        manual.write_new_data()

    db.drop_collection(test_collection_name)
