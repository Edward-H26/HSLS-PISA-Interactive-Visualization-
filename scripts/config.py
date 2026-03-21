import json
from pathlib import Path

import altair as alt
import pandas as pd

alt.data_transformers.disable_max_rows()

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "json"
OUTPUT_DIR.mkdir(parents = True, exist_ok = True)

DARK_CONFIG = {
    "background": "#030712",
    "view": {"stroke": "transparent"},
    "axis": {
        "labelColor": "#E0E0E0",
        "titleColor": "#FFFFFF",
        "gridColor": "#333333",
        "domainColor": "#444444",
        "tickColor": "#444444",
    },
    "legend": {"labelColor": "#E0E0E0", "titleColor": "#FFFFFF"},
    "title": {"color": "#FFFFFF", "subtitleColor": "#B0B0B0"},
}

OECD_COUNTRIES = {
    "AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "COL", "CRI", "CZE", "DEU",
    "DNK", "ESP", "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISL",
    "ITA", "JPN", "KOR", "LTU", "LVA", "MEX", "NLD", "NOR", "NZL", "POL",
    "PRT", "SVK", "SVN", "SWE", "TUR", "USA",
}

COUNTRY_NAME_MAP = {
    "USA": "United States", "GBR": "United Kingdom", "DEU": "Germany",
    "FRA": "France", "JPN": "Japan", "KOR": "South Korea", "AUS": "Australia",
    "CAN": "Canada", "NLD": "Netherlands", "SWE": "Sweden", "NOR": "Norway",
    "FIN": "Finland", "DNK": "Denmark", "CHE": "Switzerland", "AUT": "Austria",
    "BEL": "Belgium", "IRL": "Ireland", "NZL": "New Zealand", "SGP": "Singapore",
    "HKG": "Hong Kong", "MAC": "Macao", "TWN": "Taiwan", "ISR": "Israel",
    "POL": "Poland", "CZE": "Czech Republic", "SVN": "Slovenia", "EST": "Estonia",
    "LVA": "Latvia", "LTU": "Lithuania", "HUN": "Hungary", "SVK": "Slovakia",
    "PRT": "Portugal", "ESP": "Spain", "ITA": "Italy", "GRC": "Greece",
    "TUR": "Turkey", "CHL": "Chile", "MEX": "Mexico", "BRA": "Brazil",
    "ARG": "Argentina", "COL": "Colombia", "PER": "Peru", "URY": "Uruguay",
}

CONTINENT_MAP = {
    "USA": "North America", "CAN": "North America", "MEX": "North America", "PAN": "North America",
    "CRI": "North America", "DOM": "North America", "JAM": "North America", "PRI": "North America",
    "BRA": "South America", "ARG": "South America", "CHL": "South America", "COL": "South America",
    "PER": "South America", "URY": "South America", "ECU": "South America",
    "GBR": "Europe", "FRA": "Europe", "DEU": "Europe", "ESP": "Europe", "ITA": "Europe",
    "PRT": "Europe", "NLD": "Europe", "BEL": "Europe", "LUX": "Europe", "CHE": "Europe",
    "AUT": "Europe", "SWE": "Europe", "NOR": "Europe", "DNK": "Europe", "FIN": "Europe",
    "ISL": "Europe", "IRL": "Europe", "POL": "Europe", "CZE": "Europe", "SVK": "Europe",
    "HUN": "Europe", "SVN": "Europe", "EST": "Europe", "LVA": "Europe", "LTU": "Europe",
    "GRC": "Europe", "TUR": "Europe", "ROU": "Europe", "BGR": "Europe", "HRV": "Europe",
    "SRB": "Europe", "MNE": "Europe", "ALB": "Europe", "BIH": "Europe", "MKD": "Europe",
    "CHN": "Asia", "HKG": "Asia", "MAC": "Asia", "TWN": "Asia", "JPN": "Asia", "KOR": "Asia",
    "SGP": "Asia", "THA": "Asia", "VNM": "Asia", "IDN": "Asia", "MYS": "Asia", "PHL": "Asia",
    "KAZ": "Asia", "QAT": "Asia", "ARE": "Asia", "SAU": "Asia", "JOR": "Asia", "LBN": "Asia",
    "KWT": "Asia", "OMN": "Asia", "BHR": "Asia", "IND": "Asia", "PAK": "Asia", "BGD": "Asia",
    "LAO": "Asia", "KHM": "Asia",
    "ZAF": "Africa", "MAR": "Africa", "TUN": "Africa", "EGY": "Africa", "SEN": "Africa",
    "AUS": "Oceania", "NZL": "Oceania", "FJI": "Oceania",
}

INTERNET_USAGE_MAP = {
    0: "None",
    1: "1-2h",
    2: "2-4h",
    3: "4-6h",
    4: "6-8h",
    5: "8-10h",
    6: "10-12h",
    7: "12-14h",
    8: "14-16h",
    9: "16+h",
    10: "Extreme",
}


def load_dataset(filename, *, columns = None, low_memory = False, nrows = None):
    return pd.read_csv(DATA_DIR / filename, usecols = columns, low_memory = low_memory, nrows = nrows)


def get_available_columns(filename, candidates):
    header = load_dataset(filename, nrows = 0)
    return [column for column in candidates if column in header.columns]


def map_continent(values):
    return values.map(CONTINENT_MAP).fillna("Other")


def sample_group_rows(df, group_columns, sample_size, *, seed = 42):
    return (
        df.groupby(group_columns, group_keys = False)
        .apply(lambda frame: frame.sample(n = min(sample_size, len(frame)), random_state = seed), include_groups = False)
        .reset_index(drop = True)
    )


def save_chart(chart, filename):
    spec = json.loads(chart.to_json())
    spec["config"] = DARK_CONFIG

    with open(OUTPUT_DIR / filename, "w", encoding = "utf-8") as output_file:
        json.dump(spec, output_file, indent = 2)
