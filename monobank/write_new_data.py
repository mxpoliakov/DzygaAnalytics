from datetime import datetime

from common.mongo import get_last_document_datetime
from common.mongo import write_df_to_collection_with_logs
from monobank.common import get_access_token_and_account_id
from monobank.common import get_monobank_api_data


def write_new_data(creds_key, donation_source="Monobank"):
    access_token, account_id = get_access_token_and_account_id(creds_key)
    last_document_datetime = get_last_document_datetime(donation_source, convert_to_str=False)
    df = get_monobank_api_data(access_token, account_id, last_document_datetime)

    write_df_to_collection_with_logs(
        df,
        last_document_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        donation_source=donation_source,
        insertion_mode="Auto",
    )
