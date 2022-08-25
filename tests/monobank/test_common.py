import json

import requests

from common.config import get_creds_keys_list
from monobank.common import MONOBANK_ENDPOINT_URL
from monobank.common import get_access_token_and_account_id


def test_get_access_token():
    creds_key = get_creds_keys_list("Monobank").pop()
    access_token, account_id = get_access_token_and_account_id(creds_key)
    response = requests.get(
        f"{MONOBANK_ENDPOINT_URL}/personal/client-info",
        headers={"Content-Type": "application/json", "X-Token": access_token},
    )
    assert response.status_code == requests.codes["ok"], response.text
    response = json.loads(response.text)

    account_title = None
    for jar in response["jars"]:
        if jar["id"] == account_id:
            account_title = jar["title"]

    assert account_title == "Dzyga’s Paw 🐾"
