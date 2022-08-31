"""This module contains class for Manual donation source"""
import pandas as pd

from sources.base import SourceBase


class Manual(SourceBase):
    """A class that allows inserting the data manually from the csv.
    Useful for tracking rarely updated sources or cash.

    Parameters
    ----------
    creds_key : str
        The credential key for the source to access secret environment variables
    donation_source : str
        The donation source name
    filepath : str
        The csv data path to write
    """

    def __init__(self, creds_key: str, donation_source: str, filepath: str):
        super().__init__(creds_key, donation_source)
        self.insertion_mode = "Manual"
        self.start_datetime = None
        self.end_datetime = None
        self.filepath = filepath

    def get_api_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.filepath, parse_dates=["datetime"])
        df["senderNote"] = df["senderNote"].fillna("")
        df = df.where(pd.notnull(df), None)
        return df
