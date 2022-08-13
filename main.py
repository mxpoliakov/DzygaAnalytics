from paypal.write_new_data import write_new_data


def update_dashboard(event, context):
    write_new_data(creds_key="paypal_dimko", donation_source="PayPal")
