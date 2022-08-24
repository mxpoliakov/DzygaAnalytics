import pytest

from paypal.write_new_data import get_access_token


@pytest.mark.parametrize("creds_key", ["PAYPAL_DIMKO", "PAYPAL_ROMAN"])
def test_get_access_token(creds_key):
    assert isinstance(get_access_token(creds_key), str)
