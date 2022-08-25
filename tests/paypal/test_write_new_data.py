import pytest

from common.config import get_creds_keys_list
from paypal.write_new_data import get_access_token


@pytest.mark.parametrize("creds_key", get_creds_keys_list("PayPal"))
def test_get_access_token(creds_key):
    assert isinstance(get_access_token(creds_key), str)
