from pymongo import MongoClient

from common.get_creds import get_creds


def write_df_to_collection_with_logs(
    df, last_document_datetime, current_datetime, donation_source="PayPal", insertion_mode="Manual"
):
    base_str = f"{last_document_datetime} - {current_datetime} | {donation_source} |"
    if not df.empty:
        write_df_to_collection(df, donation_source, insertion_mode)
        print(f"{base_str} Wrote {len(df)} rows")
    else:
        print(f"{base_str} | No data")


def write_df_to_collection(df, donation_source="PayPal", insertion_mode="Manual"):
    client = MongoClient(get_creds()["mongo"]["uri"])
    conn = client["AppDB"]
    rows_to_insert = []
    for _, row in df.iterrows():
        row_insert = {
            "donationSource": donation_source,
            "senderName": row["Name"],
            "senderEmail": row["Email"],
            "currency": row["Currency"],
            "amountUSD": row["Converted Sum"],
            "amountOriginal": row["Original Sum"],
            "senderNote": row["Note"],
            "datetime": row["Datetime"].to_pydatetime(),
            "insertionMode": insertion_mode,
        }
        rows_to_insert.append(row_insert)

    conn.get_collection("donations").insert_many(rows_to_insert)
