from datetime import datetime

import pytest

from common.mongo import get_collection
from common.mongo import get_last_document_datetime


def test_connection_to_mongo():
    assert get_collection().name == "donations"

@pytest.mark.parametrize("convert_to_str", [True, False])
@pytest.mark.parametrize("donation_source", ["Dimko's PayPal", "Roman's PayPal", "Dzyga's Paw Jar"])
def test_get_last_document_datetime(convert_to_str, donation_source):
    last_document_datetime = get_last_document_datetime(donation_source, convert_to_str)
    assert type(last_document_datetime) == str if convert_to_str else datetime