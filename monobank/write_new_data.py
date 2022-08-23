import argparse
from datetime import datetime

from common.get_last_document_datetime import get_last_document_datetime
from common.write_df_to_collection import write_df_to_collection
from monobank.monobank_common import get_access_token_and_account_id
from monobank.monobank_common import get_monobank_api_data


def write_new_data(creds_key, donation_source="Monobank"):
    access_token, account_id = get_access_token_and_account_id(creds_key)
    last_document_datetime = get_last_document_datetime(donation_source, convert_to_str=False)
    df = get_monobank_api_data(access_token, account_id, last_document_datetime)

    current_datetime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    if not df.empty:
        write_df_to_collection(df, donation_source, insertion_mode="Auto")
        print(
            f"{last_document_datetime} - {current_datetime} | {donation_source} | Wrote {len(df)} rows"
        )
    else:
        print(f"{last_document_datetime} - {current_datetime} | {donation_source} | No data")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--creds_key", type=str, required=True)
    parser.add_argument("-d", "--donation_source", type=str, default="Monobank", required=False)
    args = parser.parse_args()
    write_new_data(args.creds_key, args.donation_source)
