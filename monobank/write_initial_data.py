import argparse
from datetime import datetime

from common.mongo import write_df_to_collection
from monobank.common import get_access_token_and_account_id
from monobank.common import get_monobank_api_data

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--creds_key", type=str, required=True)
    parser.add_argument("-d", "--donation_source", type=str, default="Monobank", required=False)

    args = parser.parse_args()
    access_token, account_id = get_access_token_and_account_id(args.creds_key)
    start_datetime = datetime(2022, 7, 1)
    end_datetime = datetime(2022, 8, 1)
    df = get_monobank_api_data(access_token, account_id, start_datetime, end_datetime)
    write_df_to_collection(df, args.donation_source, insertion_mode="Manual")
