from common.config import get_sources
from sources.base import SourceBase
from sources.monobank import Monobank
from sources.paypal import PayPal


def get_source_class(source_type: str) -> SourceBase:
    class_map = {"PayPal": PayPal, "Monobank": Monobank}
    return class_map[source_type]


def update_dashboard(event, context):
    _ = event
    _ = context

    for source_dict in get_sources():
        source_class = get_source_class(source_dict["type"])
        source_class(
            creds_key=source_dict["creds_key"], donation_source=source_dict["name"]
        ).write_new_data()
