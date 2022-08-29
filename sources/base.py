from abc import ABC
from abc import abstractmethod
from datetime import datetime
from datetime import timedelta

import pandas as pd

from common.config import get_source
from common.mongo import get_last_document_datetime
from common.mongo import write_df_to_collection_with_logs

DELTA_TIME_PERIOD = timedelta(days=25)


class SourceBase(ABC):
    def __init__(self, creds_key: str, donation_source: str):
        self.creds_key = creds_key
        self.donation_source = donation_source

    def is_start_datetime_creation_date(self, start_datetime: datetime) -> bool:
        return start_datetime == get_source(self.donation_source)["creation_date"]

    @abstractmethod
    def get_api_data(self, start_datetime: datetime, end_datetime: datetime) -> pd.DataFrame:
        pass

    def write_new_data(self) -> None:
        start_datetime = get_last_document_datetime(self.donation_source)
        end_datetime = datetime.utcnow()
        if end_datetime - start_datetime > DELTA_TIME_PERIOD:
            end_datetime = start_datetime + DELTA_TIME_PERIOD
        df = self.get_api_data(start_datetime, end_datetime)
        write_df_to_collection_with_logs(
            df,
            start_datetime,
            end_datetime,
            donation_source=self.donation_source,
            insertion_mode="Auto",
        )
