from common.config import get_sources
from monobank.write_new_data import write_new_data as write_new_data_monobank
from paypal.write_new_data import write_new_data as write_new_data_paypal


def update(event, context):
    _ = event
    _ = context

    for source in get_sources():
        match source["type"]:
            case "PayPal":
                write_new_data = write_new_data_paypal
            case "Monobank":
                write_new_data = write_new_data_monobank

        write_new_data(creds_key=source["creds_key"], donation_source=source["name"])
