"""This module contains tests for GCP Cloud Function entrypoint"""
from unittest.mock import call
from unittest.mock import patch

from common.config import get_sources
from main import update_dashboard
from sources.monobank import Monobank
from sources.paypal import PayPal


def test_update_dashboard() -> None:
    """Tests update_dashboard entrypoint"""
    with (
        patch("main.Monobank", spec=Monobank) as write_new_data_monobank_mock,
        patch("main.PayPal", spec=PayPal) as write_new_data_paypal_mock,
    ):
        update_dashboard()

        paypal_calls = []
        monobank_calls = []

        for source in get_sources():
            call_signature = call(creds_key=source["creds_key"], donation_source=source["name"])
            match source["type"]:
                case "PayPal":
                    paypal_calls.append(call_signature)
                case "Monobank":
                    monobank_calls.append(call_signature)
        assert write_new_data_paypal_mock.return_value.write_new_data.call_count == len(
            paypal_calls
        )
        assert write_new_data_monobank_mock.return_value.write_new_data.call_count == len(
            monobank_calls
        )
        assert write_new_data_paypal_mock.call_args_list == paypal_calls
        assert write_new_data_monobank_mock.call_args_list == monobank_calls
