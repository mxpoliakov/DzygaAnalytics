"""This module contains tests for GCP Cloud Function entrypoint"""
from unittest.mock import PropertyMock
from unittest.mock import call
from unittest.mock import patch

from common.config import get_sources
from common.constants import DEFAULT_USD_UAH_CONVERTION_RATE
from main import update_dashboard
from sources.monobank import Monobank
from sources.paypal import PayPal
from sources.privatbank import Privatbank


def test_update_dashboard() -> None:
    """Tests update_dashboard entrypoint"""
    with (
        patch(
            "sources.base.SourceBase.usd_to_uah_current_rate",
            PropertyMock(return_value=DEFAULT_USD_UAH_CONVERTION_RATE),
        ),
        patch("main.Monobank", spec=Monobank) as write_new_data_monobank_mock,
        patch("main.PayPal", spec=PayPal) as write_new_data_paypal_mock,
        patch("main.Privatbank", spec=Privatbank) as write_new_data_privatbank_mock,
    ):
        update_dashboard()

        paypal_calls = []
        monobank_calls = []
        privatbank_calls = []

        for source in get_sources():
            call_signature = call(source["name"])
            match source["type"]:
                case "PayPal":
                    paypal_calls.append(call_signature)
                case "Monobank":
                    monobank_calls.append(call_signature)
                case "Privatbank":
                    privatbank_calls.append(call_signature)

        assert write_new_data_paypal_mock.return_value.write_new_data.call_count == len(
            paypal_calls
        )
        assert write_new_data_monobank_mock.return_value.write_new_data.call_count == len(
            monobank_calls
        )
        assert write_new_data_privatbank_mock.return_value.write_new_data.call_count == len(
            privatbank_calls
        )
        assert write_new_data_paypal_mock.call_args_list == paypal_calls
        assert write_new_data_monobank_mock.call_args_list == monobank_calls
        assert write_new_data_privatbank_mock.call_args_list == privatbank_calls
