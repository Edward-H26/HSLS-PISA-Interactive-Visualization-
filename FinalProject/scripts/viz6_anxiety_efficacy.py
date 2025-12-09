import pandas as pd
import altair as alt
import numpy as np
from config import DATA_DIR, save_chart, OECD_COUNTRIES

alt.data_transformers.disable_max_rows()

pisa_cols = ["CNT", "ICTRES", "MATHEFF", "MATHPERS", "PV1MATH", "ST004D01T", "IC170Q01JA", "IC170Q02JA", "ESCS", "LANGN"]
hsls_cols = ["X1SES", "X1MTHEFF", "X1TXMTSCOR", "X1SEX", "X1MTHINT", "S1WEBINFO"]

pisa_header = pd.read_csv(DATA_DIR / "pisa_subset.csv", nrows=0).columns
pisa_use = [c for c in pisa_cols if c in pisa_header]
pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", usecols=pisa_use)
hsls_df = pd.read_csv(DATA_DIR / "hsls_subset.csv", usecols=[c for c in hsls_cols if c in pd.read_csv(DATA_DIR/"hsls_subset.csv", nrows=0).columns])

continent_map = {
    "USA": "North America", "CAN": "North America", "MEX": "North America", "PAN": "North America", "CRI": "North America", "DOM": "North America",
    "JAM": "North America", "PRI": "North America", "BRA": "South America", "ARG": "South America", "CHL": "South America", "COL": "South America",
    "PER": "South America", "URY": "South America", "ECU": "South America",
    "GBR": "Europe", "FRA": "Europe", "DEU": "Europe", "ESP": "Europe", "ITA": "Europe", "PRT": "Europe", "NLD": "Europe", "BEL": "Europe",
    "LUX": "Europe", "CHE": "Europe", "AUT": "Europe", "SWE": "Europe", "NOR": "Europe", "DNK": "Europe", "FIN": "Europe", "ISL": "Europe",
    "IRL": "Europe", "POL": "Europe", "CZE": "Europe", "SVK": "Europe", "HUN": "Europe", "SVN": "Europe", "EST": "Europe", "LVA": "Europe",
    "LTU": "Europe", "GRC": "Europe", "TUR": "Europe", "ROU": "Europe", "BGR": "Europe", "HRV": "Europe", "SRB": "Europe", "MNE": "Europe",
    "ALB": "Europe", "BIH": "Europe", "MKD": "Europe",
    "CHN": "Asia", "HKG": "Asia", "MAC": "Asia", "TWN": "Asia", "JPN": "Asia", "KOR": "Asia", "SGP": "Asia", "THA": "Asia",
    "VNM": "Asia", "IDN": "Asia", "MYS": "Asia", "PHL": "Asia", "KAZ": "Asia", "QAT": "Asia", "ARE": "Asia", "SAU": "Asia",
    "JOR": "Asia", "LBN": "Asia", "KWT": "Asia", "OMN": "Asia", "BHR": "Asia", "IND": "Asia", "PAK": "Asia", "BGD": "Asia",
    "LAO": "Asia", "KHM": "Asia",
    "ZAF": "Africa", "MAR": "Africa", "TUN": "Africa", "EGY": "Africa", "SEN": "Africa",
    "AUS": "Oceania", "NZL": "Oceania", "FJI": "Oceania"
}

pisa_df = pisa_df.assign(stem_interest=pisa_df.get("MATHPERS"))
if "IC170Q01JA" in pisa_df.columns and "IC170Q02JA" in pisa_df.columns:
    pisa_df["ict_behavior"] = pisa_df[["IC170Q01JA", "IC170Q02JA"]].mean(axis=1)
elif "IC170Q01JA" in pisa_df.columns:
    pisa_df["ict_behavior"] = pisa_df["IC170Q01JA"]
else:
    pisa_df["ict_behavior"] = np.nan

country_language_map = {
    "USA": 313, "GBR": 313, "AUS": 313, "NZL": 313, "CAN": 313, "IRL": 313, "JAM": 313,
    "ESP": 156, "MEX": 156, "ARG": 156, "CHL": 156, "COL": 156, "PER": 156, "URY": 156, "ECU": 156, "PAN": 156, "CRI": 156, "DOM": 156,
    "BRA": 232, "PRT": 232,
    "FRA": 125, "BEL": 125,
    "DEU": 130, "AUT": 130, "CHE": 130, "LUX": 130,
    "ITA": 148,
    "NLD": 104,
    "POL": 233,
    "CZE": 61,
    "SVK": 276,
    "HUN": 137,
    "SVN": 277,
    "EST": 114,
    "LVA": 166,
    "LTU": 170,
    "GRC": 133,
    "TUR": 308,
    "ROU": 244,
    "BGR": 46,
    "HRV": 58,
    "SRB": 269,
    "ALB": 2,
    "SWE": 295,
    "NOR": 215,
    "DNK": 63,
    "FIN": 120,
    "ISL": 139,
    "JPN": 153,
    "KOR": 160,
    "CHN": 55, "HKG": 55, "MAC": 55, "TWN": 55,
    "THA": 303,
    "VNM": 326,
    "IDN": 141,
    "MYS": 185,
    "SGP": 313,
    "PHL": 313,
    "KAZ": 155,
    "QAT": 8, "ARE": 8, "SAU": 8, "JOR": 8, "LBN": 8, "KWT": 8, "OMN": 8, "BHR": 8,
    "MAR": 8, "TUN": 8, "EGY": 8,
    "ZAF": 313,
}

pisa_df = pisa_df.assign(
    source="PISA",
    continent=lambda d: d["CNT"].map(continent_map).fillna("Other"),
    gender=lambda d: d.get("ST004D01T", pd.Series(index=d.index)).map({1: "Female", 2: "Male"}),
    ict_resource=lambda d: d.get("ICTRES", pd.Series(index=d.index)),
    OECD_Status=lambda d: d["CNT"].apply(lambda x: "OECD" if x in OECD_COUNTRIES else "Non-OECD")
)

if "LANGN" in pisa_df.columns:
    pisa_df["test_lang"] = pisa_df["CNT"].map(country_language_map)
    pisa_df["language_match"] = (pisa_df["LANGN"] == pisa_df["test_lang"]).map({True: "Same Language", False: "Different Language"})
else:
    pisa_df["language_match"] = "Same Language"

escs_terciles = pisa_df["ESCS"].quantile([0.33, 0.67]).values
pisa_df["SES_Level"] = pd.cut(
    pisa_df["ESCS"],
    bins=[-np.inf, escs_terciles[0], escs_terciles[1], np.inf],
    labels=["Low SES", "Mid SES", "High SES"]
)
pisa_df["OECD_SES"] = pisa_df["OECD_Status"] + " " + pisa_df["SES_Level"].astype(str)

hsls_df = hsls_df.assign(
    CNT="USA",
    source="HSLS",
    continent="North America",
    gender=lambda d: d["X1SEX"].map({1: "Male", 2: "Female"}),
    stem_interest=lambda d: d["X1MTHINT"],
    ict_resource=lambda d: d["X1SES"],
    ict_behavior=lambda d: d.get("S1WEBINFO", pd.Series(index=d.index)),
    OECD_Status="OECD",
    language_match="Same Language"
)

hsls_ses_terciles = hsls_df["X1SES"].quantile([0.33, 0.67]).values
hsls_df["SES_Level"] = pd.cut(
    hsls_df["X1SES"],
    bins=[-np.inf, hsls_ses_terciles[0], hsls_ses_terciles[1], np.inf],
    labels=["Low SES", "Mid SES", "High SES"]
)
hsls_df["OECD_SES"] = "OECD " + hsls_df["SES_Level"].astype(str)

left_base = pd.concat([
    pisa_df[["continent", "ict_resource", "stem_interest", "source"]],
    hsls_df[["continent", "ict_resource", "stem_interest", "source"]],
], ignore_index=True)
left_base = left_base.dropna(subset=["ict_resource", "stem_interest", "continent", "source"])
left_base["z_resource"] = left_base.groupby("source")["ict_resource"].transform(lambda x: (x - x.mean()) / x.std(ddof=0))
left_base["z_stem"] = left_base.groupby("source")["stem_interest"].transform(lambda x: (x - x.mean()) / x.std(ddof=0))
v6_continent_df = (
    left_base.groupby("continent")
    .agg(avg_res=("z_resource", "mean"), avg_stem=("z_stem", "mean"), n=("z_resource", "size"))
    .reset_index()
)

pisa_students = pisa_df[["continent", "language_match", "ict_behavior", "stem_interest", "source"]].dropna()
hsls_students = hsls_df[["continent", "language_match", "ict_behavior", "stem_interest", "source"]].dropna()
v6_students_df = pd.concat([pisa_students, hsls_students], ignore_index=True)
v6_students_df = v6_students_df[~v6_students_df["ict_behavior"].isin([-9, -8, -7, -5])]

v6_continent_select = alt.selection_point(fields=["continent"], name="v6_continent_select")

v6_left_chart = (
    alt.Chart(v6_continent_df)
    .mark_circle(size=150)
    .encode(
        x=alt.X("avg_res:Q", title="Mean ICT Resources (z within source)", scale=alt.Scale(domain=[-1.0, 1.0])),
        y=alt.Y("avg_stem:Q", title="Mean STEM Interest (z within source)", scale=alt.Scale(domain=[-0.4, 0.2])),
        color=alt.Color("continent:N", title="Continent/Region"),
        opacity=alt.condition(v6_continent_select, alt.value(1), alt.value(0.5)),
        tooltip=["continent", "avg_res", "avg_stem"],
    )
    .add_params(v6_continent_select)
    .properties(
        title={"text": "STEM Interest vs ICT Resources by Continent", "subtitle": "Click continent to filter right plot",
               "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
        width=450, height=400
    )
)

v6_right_chart = (
    alt.Chart(v6_students_df)
    .transform_filter(v6_continent_select)
    .transform_density(
        density="ict_behavior",
        groupby=["language_match"],
        as_=["ict_behavior", "density"],
        bandwidth=0.25,
    )
    .mark_area(opacity=0.5)
    .encode(
        x=alt.X("ict_behavior:Q", title="ICT Behavior (proxy)"),
        y=alt.Y("density:Q", title="Density"),
        color=alt.Color("language_match:N",
                       scale=alt.Scale(domain=["Same Language", "Different Language"], range=["#4CAF50", "#FF9800"]),
                       title="Test Language"),
        tooltip=["language_match:N", "ict_behavior:Q", "density:Q"],
    )
    .properties(
        title={"text": "ICT Behavior Distribution by Test Language Match", "subtitle": "Filtered by selected continent",
               "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
        width=400, height=400
    )
)

viz6 = alt.hconcat(v6_left_chart, v6_right_chart).resolve_scale(color="independent")
save_chart(viz6, "combined_parent_education.json")
