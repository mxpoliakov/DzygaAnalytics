from monobank.write_new_data import write_new_data as write_new_data_monobank
from paypal.write_new_data import write_new_data as write_new_data_paypal


def update_dashboard(event, context):
    write_new_data_paypal(creds_key="paypal_dimko", donation_source="Dimko's PayPal")
    write_new_data_paypal(creds_key="paypal_roman", donation_source="Roman's PayPal")
    write_new_data_monobank(creds_key="monobank_jar_dimko", donation_source="Dzyga's Paw Jar")
