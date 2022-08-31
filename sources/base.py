"""This module contains base class for donation source"""
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from datetime import timedelta

import pandas as pd
from pymongo import DESCENDING

from common.config import get_source
from common.mongo import get_collection

DELTA_TIME_PERIOD = timedelta(days=25)


class SourceBase(ABC):
    """A base class that defines common logic for a donation source.

    Parameters
    ----------
    creds_key : str
        The credential key for the source to access secret environment variables
    donation_source: str
        The donation source name
    """

    def __init__(self, creds_key: str, donation_source: str):
        self.creds_key = creds_key
        self.donation_source = donation_source

        self.collection = get_collection()
        self.insertion_mode = "Auto"

        self.start_datetime, self.is_source_creation_date = self.get_last_document_datetime()
        self.end_datetime = datetime.utcnow()

        if self.end_datetime - self.start_datetime > DELTA_TIME_PERIOD:
            # In the most cases APIs do not support retrieving
            # transaction data for more than 30 days.
            # If the difference between start and end dates
            # is more than DELTA_TIME_PERIOD, the end date is set to start date + DELTA_TIME_PERIOD.
            # After multiple retrievals, we eventually would catch up to the current datetime.
            self.end_datetime = self.start_datetime + DELTA_TIME_PERIOD

    def get_last_document_datetime(self) -> tuple[datetime, bool]:
        """Returns last document datetime found for a donation source.
        If no such document exist returns the specified donation source
        creation date from the config file

        Returns
        -------
        tuple[datetime, bool]
            The last document datetime or donation source creation date.
            Also returns an indication if the returned datetime is source creation date
        """
        last_document = self.collection.find_one(
            {"donationSource": self.donation_source}, sort=[("datetime", DESCENDING)]
        )
        if last_document is None:
            return get_source(self.donation_source)["creation_date"], True

        return last_document["datetime"], False

    @abstractmethod
    def get_api_data(self) -> pd.DataFrame:
        """An abstract method to get API data for donation source
        Each source should overload this methods and return parsed transaction data
        in a common form

        Returns
        -------
        pd.DataFrame
            Returns a pd.DataFrame with transaction data
        """

    def mask_name(self, name: None | str, chars_to_keep: int = 2) -> str:
        """Censores sender name. For example, Test Person -> Te** Pe****

        Parameters
        ----------
        name : None | str
            A name to censor. Can be None
        chars_to_keep : int, optional
            How many first characters in each word to keep, by default 2

        Returns
        -------
        str
            Censored name.
        """
        if isinstance(name, str):
            return " ".join(
                [word[:chars_to_keep] + "*" * len(word[chars_to_keep:]) for word in name.split()]
            )
        return ""

    def write_df_to_collection(self, df: pd.DataFrame) -> None:
        """Writes pd.DataFrame with the API data to collection

        Parameters
        ----------
        df : pd.DataFrame
            pd.DataFrame with the API data
        """

        base_str = f"{self.start_datetime} - {self.end_datetime} | {self.donation_source} |"
        if not df.empty:
            df["donationSource"] = self.donation_source
            df["insertionMode"] = self.insertion_mode
            df["datetime"] = pd.Series(df["datetime"].dt.to_pydatetime(), dtype=object)
            df["senderNameCensored"] = df["senderName"].apply(self.mask_name)
            self.collection.insert_many(df.to_dict("records"))
            print(f"{base_str} Wrote {len(df)} rows")
        else:
            print(f"{base_str} No data")

    def write_new_data(self) -> None:
        """Fetches and writes new API data to the collection"""
        df = self.get_api_data()
        self.write_df_to_collection(df)
