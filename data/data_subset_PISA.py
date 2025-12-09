import zipfile
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent
ZIP_PATH = DATA_DIR / "PISA2022.zip"
CSV_NAME = "PISA2022.csv"
OUTPUT_PATH = DATA_DIR / "pisa_subset.csv"

SELECTED_COLUMNS = [
    "CNT",
    "CNTSCHID",
    "W_FSTUWT",
    "STRATUM",
    "ST004D01T",
    "AGE",
    "ST019AQ01T",
    "IMMIG",
    "LANGN",
    "ESCS",
    "HOMEPOS",
    "WEALTH",
    "CULTPOSS",
    "HEDRES",
    "ICTRES",
    "ST255Q01JA",
    "HISCED",
    "PARED",
    "BFMJ2",
    "HISEI",
    "BMMJ1",
    "ST253Q01JA",
    "ST253Q02JA",
    "ST253Q04JA",
    "ST250Q03JA",
    "ST250Q02JA",
    "ST250Q04JA",
    "ST250Q01JA",
    "ST258Q01JA",
    "ST261Q01JA",
    "ST261Q04JA",
    "ST261Q06JA",
    "ST261Q03JA",
    "BELONG",
    "ST062Q01TA",
    "ST062Q02TA",
    "MATHEFF",
    "ANXMAT",
    "MATHPERS",
    "JOYREAD",
    "ST188Q01HA",
    "ST265Q01JA",
    "ST265Q03JA",
    "IC011Q02TA",
    "ICTSCH",
    "ST225Q06JA",
    "EXPHISCED",
    "PV1MATH",
    "PV2MATH",
    "PV3MATH",
    "PV4MATH",
    "PV5MATH",
    "PV6MATH",
    "PV7MATH",
    "PV8MATH",
    "PV9MATH",
    "PV10MATH",
    "PV1READ",
    "PV1SCIE",
    "ST016Q01NA",
    "ST292Q01JA",
    "ST292Q02JA",
    "ST292Q03JA",
    "ST292Q04JA",
    "ST292Q05JA",
    "ST292Q06JA",
    "IC170Q01JA",
    "IC170Q02JA",
    "ST268Q01JA",
    "ST268Q03JA",
    "ST268Q04JA",
    "ST268Q06JA",
    "ST263Q02JA",
    "ST263Q04JA",
    "INSCIE",
    "PAREDINT",
]


def create_subset():
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        with z.open(CSV_NAME) as f:
            df_full = pd.read_csv(f, low_memory = False, nrows = 0)
            available_cols = [col for col in SELECTED_COLUMNS if col in df_full.columns]

    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        with z.open(CSV_NAME) as f:
            df_subset = pd.read_csv(f, usecols = available_cols, low_memory = False)

    df_subset.to_csv(OUTPUT_PATH, index = False)
    return df_subset


if __name__ == "__main__":
    df = create_subset()
