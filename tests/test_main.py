from unittest.mock import call
from unittest.mock import patch

from common.config import get_sources
from main import update_dashboard


def test_update():
    with (
        patch("main.write_new_data_monobank", return_value=None) as write_new_data_monobank_mock,
        patch("main.write_new_data_paypal", return_value=None) as write_new_data_paypal_mock,
    ):
        update_dashboard(None, None)

        paypal_calls = []
        monobank_calls = []

        for source in get_sources():
            call_signature = call(creds_key=source["creds_key"], donation_source=source["name"])
            match source["type"]:
                case "PayPal":
                    paypal_calls.append(call_signature)
                case "Monobank":
                    monobank_calls.append(call_signature)

        assert write_new_data_paypal_mock.call_args_list == paypal_calls
        assert write_new_data_monobank_mock.call_args_list == monobank_calls
