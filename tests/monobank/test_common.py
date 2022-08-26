from datetime import datetime

from common.config import get_creds_keys_list
from monobank.common import get_access_token_and_account_id
from monobank.common import get_monobank_api_data


def test_get_monobank_api_data():
    creds_key = get_creds_keys_list("Monobank").pop()
    access_token, account_id = get_access_token_and_account_id(creds_key)
    start_datetime = datetime(2022, 7, 1)
    end_datetime = datetime(2022, 8, 1)
    df = get_monobank_api_data(access_token, account_id, start_datetime, end_datetime)
    assert len(df) == 3
    assert df["Original Sum"].sum() == 7500
