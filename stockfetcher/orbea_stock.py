from ftplib import FTP
import io
import pandas as pd
import numpy as np
from stockfetcher.secrets_dataclasses import FtpSecrets


class OrbeaStock:
    @staticmethod
    # @TODO split download and parsing
    def download(secrets: FtpSecrets) -> pd.DataFrame:
        ftp = FTP(secrets.host)
        file_path = "STOCKS_simpl_Izaro.csv"

        ftp.login(user=secrets.user, passwd=secrets.password)

        # Use io.BytesIO to store the file in memory
        with io.BytesIO() as memory_file:
            ftp.retrbinary(f"RETR {file_path}", memory_file.write)
            # Move the cursor to the beginning of the BytesIO object
            memory_file.seek(0)
            # Read the content of the file
            file_content = memory_file.read()

        dtypes = {
            "TTCC": str,
            "Available": np.int64,
            "Dunno": str,
            "Date": str,
            "EAN": str,
            "Empty": str,
        }

        df = pd.read_csv(
            io.StringIO(file_content.decode("utf-8")),
            dtype=dtypes,
            sep=";",
            names=list(map(lambda x: x, dtypes.keys())),
        )

        df.drop(columns=["TTCC", "Date", "Dunno", "Empty"], axis=1, inplace=True)

        return df
