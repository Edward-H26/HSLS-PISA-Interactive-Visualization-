import altair as alt
import numpy as np
import pandas as pd

from config import OECD_COUNTRIES, get_available_columns, load_dataset, map_continent, sample_group_rows, save_chart

alt.data_transformers.disable_max_rows()

PISA_COLUMNS = ["CNT", "ICTRES", "MATHEFF", "MATHPERS", "PV1MATH", "ST004D01T", "IC170Q01JA", "IC170Q02JA", "ESCS", "LANGN"]
HSLS_COLUMNS = ["X1SES", "X1MTHEFF", "X1TXMTSCOR", "X1SEX", "X1MTHINT", "S1WEBINFO"]

pisa_df = load_dataset("pisa_subset.csv", columns = get_available_columns("pisa_subset.csv", PISA_COLUMNS))
hsls_df = load_dataset("hsls_subset.csv", columns = get_available_columns("hsls_subset.csv", HSLS_COLUMNS))

pisa_df = pisa_df.assign(stem_interest = pisa_df.get("MATHPERS"))

if {"IC170Q01JA", "IC170Q02JA"}.issubset(pisa_df.columns):
    pisa_df["ict_behavior"] = pisa_df[["IC170Q01JA", "IC170Q02JA"]].mean(axis = 1)
elif "IC170Q01JA" in pisa_df.columns:
    pisa_df["ict_behavior"] = pisa_df["IC170Q01JA"]
else:
    pisa_df["ict_behavior"] = np.nan

pisa_df = pisa_df.assign(
    source = "PISA",
    continent = lambda frame: map_continent(frame["CNT"]),
    gender = lambda frame: frame.get("ST004D01T", pd.Series(index = frame.index)).map({1: "Female", 2: "Male"}),
    ict_resource = lambda frame: frame.get("ICTRES", pd.Series(index = frame.index)),
    OECD_Status = lambda frame: frame["CNT"].apply(lambda value: "OECD" if value in OECD_COUNTRIES else "Non-OECD"),
)

escs_terciles = pisa_df["ESCS"].quantile([0.33, 0.67]).values
pisa_df["SES_Level"] = pd.cut(
    pisa_df["ESCS"],
    bins = [-np.inf, escs_terciles[0], escs_terciles[1], np.inf],
    labels = ["Low SES", "Mid SES", "High SES"],
)
pisa_df["OECD_SES"] = pisa_df["OECD_Status"] + " " + pisa_df["SES_Level"].astype(str)

hsls_df = hsls_df.assign(
    CNT = "USA",
    source = "HSLS",
    continent = "North America",
    gender = lambda frame: frame["X1SEX"].map({1: "Male", 2: "Female"}),
    stem_interest = lambda frame: frame["X1MTHINT"],
    ict_resource = lambda frame: frame["X1SES"],
    ict_behavior = lambda frame: frame.get("S1WEBINFO", pd.Series(index = frame.index)),
    OECD_Status = "OECD",
)

hsls_ses_terciles = hsls_df["X1SES"].quantile([0.33, 0.67]).values
hsls_df["SES_Level"] = pd.cut(
    hsls_df["X1SES"],
    bins = [-np.inf, hsls_ses_terciles[0], hsls_ses_terciles[1], np.inf],
    labels = ["Low SES", "Mid SES", "High SES"],
)
hsls_df["OECD_SES"] = "OECD " + hsls_df["SES_Level"].astype(str)

left_base = pd.concat(
    [
        pisa_df[["continent", "ict_resource", "stem_interest", "source"]],
        hsls_df[["continent", "ict_resource", "stem_interest", "source"]],
    ],
    ignore_index = True,
).dropna(subset = ["ict_resource", "stem_interest", "continent", "source"])

left_base["z_resource"] = left_base.groupby("source")["ict_resource"].transform(lambda values: (values - values.mean()) / values.std(ddof = 0))
left_base["z_stem"] = left_base.groupby("source")["stem_interest"].transform(lambda values: (values - values.mean()) / values.std(ddof = 0))

v6_continent_df = (
    left_base.groupby("continent")
    .agg(avg_res = ("z_resource", "mean"), avg_stem = ("z_stem", "mean"), n = ("z_resource", "size"))
    .reset_index()
)

pisa_students = pisa_df[["continent", "OECD_Status", "ict_behavior", "stem_interest", "source"]].dropna()
hsls_students = hsls_df[["continent", "OECD_Status", "ict_behavior", "stem_interest", "source"]].dropna()
v6_students_df = pd.concat([pisa_students, hsls_students], ignore_index = True)
v6_students_df = v6_students_df[~v6_students_df["ict_behavior"].isin([-9, -8, -7, -5])]
v6_students_df = sample_group_rows(v6_students_df, ["continent", "OECD_Status"], 500)

v6_continent_select = alt.selection_point(fields = ["continent"], name = "v6_continent_select")

v6_left_chart = (
    alt.Chart(v6_continent_df)
    .mark_circle(size = 150)
    .encode(
        x = alt.X("avg_res:Q", title = "Mean ICT Resources (z within source)", scale = alt.Scale(domain = [-1.0, 1.0])),
        y = alt.Y("avg_stem:Q", title = "Mean STEM Interest (z within source)", scale = alt.Scale(domain = [-0.4, 0.2])),
        color = alt.Color("continent:N", title = "Continent/Region"),
        opacity = alt.condition(v6_continent_select, alt.value(1), alt.value(0.5)),
        tooltip = ["continent", "avg_res", "avg_stem"],
    )
    .add_params(v6_continent_select)
    .properties(
        title = {
            "text": "Relationship Between ICT Resources and STEM Interest",
            "subtitle": "Standardized indices by geographic region",
            "color": "#FFFFFF",
            "fontSize": 14,
            "subtitleColor": "#E0E0E0",
        },
        width = 450,
        height = 400,
    )
)

v6_right_chart = (
    alt.Chart(v6_students_df)
    .transform_filter(v6_continent_select)
    .transform_density(
        density = "ict_behavior",
        groupby = ["OECD_Status"],
        as_ = ["ict_behavior", "density"],
        bandwidth = 0.25,
    )
    .mark_area(opacity = 0.5)
    .encode(
        x = alt.X("ict_behavior:Q", title = "ICT Behavior (proxy)"),
        y = alt.Y("density:Q", title = "Density"),
        color = alt.Color(
            "OECD_Status:N",
            scale = alt.Scale(domain = ["OECD", "Non-OECD"], range = ["#4CAF50", "#FF9800"]),
            title = "OECD Status",
        ),
        tooltip = ["OECD_Status:N", "ict_behavior:Q", "density:Q"],
    )
    .properties(
        title = {
            "text": "ICT Usage Patterns: OECD vs Non-OECD Countries",
            "subtitle": "Kernel density estimates of technology engagement",
            "color": "#FFFFFF",
            "fontSize": 14,
            "subtitleColor": "#E0E0E0",
        },
        width = 400,
        height = 400,
    )
)

viz6 = (
    alt.hconcat(v6_left_chart, v6_right_chart)
    .resolve_scale(color = "independent")
    .configure_view(stroke = None, fill = None)
    .properties(background = "transparent")
)

save_chart(viz6, "combined_parent_education.json")
