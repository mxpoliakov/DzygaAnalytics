"""This module contains entry point for GCP Cloud Function"""
from common.config import get_sources
from sources.monobank import Monobank
from sources.paypal import PayPal
from sources.privatbank import Privatbank


def update_dashboard(*args, **kwargs) -> None:
    # pylint: disable=unused-argument
    """Entry point for GCP Cloud Function that updates dashboard"""
    for source_dict in get_sources("PayPal"):
        PayPal(source_dict["name"]).write_new_data()

    for source_dict in get_sources("Monobank"):
        Monobank(source_dict["name"]).write_new_data()

    for source_dict in get_sources("Privatbank"):
        Privatbank(source_dict["name"]).write_new_data()


if __name__ == "__main__":
    update_dashboard()
