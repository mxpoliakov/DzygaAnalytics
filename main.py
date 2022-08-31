"""This module contains entry point for GCP Cloud Function"""
from common.config import get_sources
from sources.monobank import Monobank
from sources.paypal import PayPal


def update_dashboard(*args, **kwargs) -> None:
    # pylint: disable=unused-argument
    """_summary_"""
    class_map = {"PayPal": PayPal, "Monobank": Monobank}
    for source_dict in get_sources():
        source_class = class_map[source_dict["type"]]
        source_class(
            creds_key=source_dict["creds_key"], donation_source=source_dict["name"]
        ).write_new_data()
