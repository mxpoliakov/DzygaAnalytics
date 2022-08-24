from monobank.write_new_data import write_new_data as write_new_data_monobank
from paypal.write_new_data import write_new_data as write_new_data_paypal


def update_dashboard(event, context):
    _ = event
    _ = context
    write_new_data_paypal(creds_key="PAYPAL_DIMKO", donation_source="Dimko's PayPal")
    write_new_data_paypal(creds_key="PAYPAL_ROMAN", donation_source="Roman's PayPal")
    write_new_data_monobank(creds_key="MONO_JAR_DIMKO", donation_source="Dzyga's Paw Jar")
