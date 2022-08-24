import json

import requests

from monobank.common import MONOBANK_ENDPOINT_URL
from monobank.common import get_access_token_and_account_id


def test_get_access_token():
    access_token, account_id = get_access_token_and_account_id("MONO_JAR_DIMKO")
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
