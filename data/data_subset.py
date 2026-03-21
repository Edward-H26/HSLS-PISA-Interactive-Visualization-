import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from data_loader import load_configured_fields

RAW_PATH = Path(__file__).parent / "hsls_17_student_pets_sr_v1_0.csv"
RAW_URL = "https://huggingface.co/datasets/ComprehensiveAnalysisOnHSLS/HSLS/resolve/main/hsls_17_student_pets_sr_v1_0.csv"
OUTPUT_PATH = Path(__file__).parent / "hsls_subset.csv"


def create_subset():
    source_path = RAW_PATH if RAW_PATH.exists() else RAW_URL
    df_subset = load_configured_fields(dataset_name = "hsls", dataset_path = source_path)
    df_subset.to_csv(OUTPUT_PATH, index = False)
    return df_subset


if __name__ == "__main__":
    create_subset()
