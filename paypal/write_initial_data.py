import argparse
import pathlib

import pandas as pd

from common.convert_currency import convert_currency
from common.write_df_to_collection import write_df_to_collection


def convert_currency_str(col):
    return col.str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)


def process_file_to_df(input_file_path):
    df = pd.read_csv(input_file_path)
    df["Datetime"] = pd.to_datetime(
        df[["Date", "Time", "TimeZone"]].agg(" ".join, axis=1), dayfirst=True
    )
    df["Email"] = df["From Email Address"]
    df = df.drop(["Date", "Time", "TimeZone", "From Email Address", "Contact Phone Number"], axis=1)
    print(f"Parsing {input_file_path} from {df.iloc[0].Datetime} to {df.iloc[-1].Datetime}")
    df["Balance"] = convert_currency_str(df["Balance"])
    df["Net"] = convert_currency_str(df["Net"])

    df = df[
        (df["Balance Impact"] == "Credit")
        & (df["Balance"] != 0)
        & (df["Type"].isin(["General Payment", "Mobile Payment"]))
    ].dropna(axis=1, how="all")

    df["Note"] = df["Note"].fillna("")
    df = df.drop(df.nunique()[df.nunique() == 1].index, axis=1)
    df["Original Sum"] = df["Net"]
    net = df.apply(
        lambda row: convert_currency(row["Net"], row["Currency"], row["Datetime"]),
        axis=1,
    )
    df["Converted Sum"] = round(net, 2)
    df = df.drop(["Balance", "Gross", "Net", "Transaction ID", "Type"], axis=1)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file_path", type=pathlib.Path, required=True)
    parser.add_argument("-d", "--donation_source", type=str, default="PayPal", required=False)
    args = parser.parse_args()
    df = process_file_to_df(args.input_file_path)
    write_df_to_collection(df, args.donation_source, "Manual")
