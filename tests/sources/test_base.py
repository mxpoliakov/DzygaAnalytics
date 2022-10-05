"""This module contains tests for base source class"""

from datetime import datetime

from sources.base import SourceBase


def test_convert_currency() -> None:
    """Tests currency_converter package"""
    assert SourceBase.convert_currency(10, "EUR", datetime(2022, 8, 20)) == 10.04
    assert SourceBase.convert_currency(10, "USD", datetime(2022, 8, 20)) == 10
    usd_to_uah_rate = SourceBase.usd_to_uah_current_rate
    assert SourceBase.convert_currency(1000, "UAH", None) == round(1000 / usd_to_uah_rate, 2)
    assert SourceBase.convert_currency(100, "UAH", None) == round(100 / usd_to_uah_rate, 2)


def test_parse_email_from_note() -> None:
    """Tests parse_email_from_note method"""
    assert SourceBase.parse_email_from_note("From: example@mail.com") == "example@mail.com"
    assert SourceBase.parse_email_from_note("Hello World!") is None
