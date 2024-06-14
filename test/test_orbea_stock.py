from unittest import TestCase
from app_secrets import ftp_secrets
from stockfetcher.orbea_stock import OrbeaStock
import numpy as np


# @TODO consider mocking
class OrbeaStockTest(TestCase):
    def test_download(self):
        expected_columns = ["EAN"]
        df = OrbeaStock.download(secrets=ftp_secrets)
        assert (
            list(df.columns) == expected_columns
        ), f"Expected columns {expected_columns} but got {list(df.columns)}"
        assert len(df) > 10, f"Expected more than 10 rows but got {len(df)}"

        expected_data_types = {
            "Available": np.int64,
            "EAN": str,
        }

        for column, expected_type in expected_data_types.items():
            assert isinstance(
                df[column].iloc[0], expected_type
            ), f"Expected column '{column}' to be of type {expected_type.__name__}"
