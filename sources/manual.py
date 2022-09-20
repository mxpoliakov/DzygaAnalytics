"""This module contains class for Manual donation source"""
import numpy as np
import pandas as pd

from sources.base import SourceBase


class Manual(SourceBase):
    """A class that allows inserting the data manually from the csv.
    Useful for tracking rarely updated sources or cash.

    Parameters
    ----------
    donation_source : str
        The donation source name
    filepath : str
        The csv data path to write
    """

    def __init__(self, donation_source: str, filepath: str):
        super().__init__(donation_source)
        self.insertion_mode = "Manual"
        self.start_datetime = None
        self.end_datetime = None
        self.filepath = filepath

    def get_api_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.filepath, parse_dates=["datetime"])
        df["senderNote"] = df["senderNote"].fillna("")
        df = df.replace({np.nan: None})
        return df
