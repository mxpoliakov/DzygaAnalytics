"""This module contains base class for donation source"""
import json
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from functools import cache

import pandas as pd
import requests
from currency_converter import ECB_URL
from currency_converter import CurrencyConverter
from pymongo import DESCENDING

from common.config import get_source
from common.constants import DEFAULT_USD_UAH_CONVERTION_RATE
from common.constants import DELTA_TIME_PERIOD
from common.constants import MONOBANK_ENDPOINT_URL
from common.constants import UAH_CODE
from common.constants import USD_CODE
from common.mongo import get_collection


class SourceBase(ABC):
    """A base class that defines common logic for a donation source.

    Parameters
    ----------
    donation_source: str
        The donation source name
    """

    def __init__(self, donation_source: str):
        self.donation_source = donation_source
        self.source_config = get_source(donation_source)
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

    @classmethod
    @property
    @cache
    def currency_converter(cls) -> CurrencyConverter:
        """
        Returns
        -------
        CurrencyConverter
            Cached instance of CurrencyConverter object
        """
        return CurrencyConverter(
            ECB_URL, fallback_on_missing_rate=True, fallback_on_wrong_date=True
        )

    @classmethod
    @property
    @cache
    def usd_to_uah_current_rate(cls) -> float:
        """currency_converter package does not support UAH,
        so we query Monobank for USD / UAH rate.
        Only real-time rate is supported, use with caution
        when converting historic UAH transactions.

        Returns
        -------
        float
            Returns USD / UAH rate for the current datetime.
        """
        response = requests.get(
            f"{MONOBANK_ENDPOINT_URL}/bank/currency",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == requests.codes["ok"], response.text
        response = json.loads(response.text)

        for rate_info in response:
            if rate_info["currencyCodeA"] == USD_CODE and rate_info["currencyCodeB"] == UAH_CODE:
                return rate_info["rateSell"]
        return DEFAULT_USD_UAH_CONVERTION_RATE

    @classmethod
    def convert_currency(cls, value: float, currency: str, date: datetime) -> float:
        """Convert currency into USD

        Parameters
        ----------
        value : float
            Transaction value
        currency : str
            Currency 3-letter code. For example, EUR
        date : datetime
            The transaction datetime

        Returns
        -------
        float
            Converted USD value
        """
        if currency != "USD":
            if currency != "UAH":
                converted_value = cls.currency_converter.convert(value, currency, "USD", date=date)
            else:
                converted_value = value / cls.usd_to_uah_current_rate
            return round(converted_value, 2)
        return value

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
            return self.source_config["creation_date"], True

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
            df["amountUSD"] = df.apply(
                lambda row: self.convert_currency(
                    row["amountOriginal"], row["currency"], row["datetime"]
                ),
                axis=1,
            )
            self.collection.insert_many(df.to_dict("records"))
            print(f"{base_str} Wrote {len(df)} rows")
        else:
            print(f"{base_str} No data")

    def write_new_data(self) -> None:
        """Fetches and writes new API data to the collection"""
        df = self.get_api_data()
        self.write_df_to_collection(df)
