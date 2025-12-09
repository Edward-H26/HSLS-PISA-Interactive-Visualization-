import pandas as pd
import altair as alt
import numpy as np
from config import DATA_DIR, save_chart, OECD_COUNTRIES

alt.data_transformers.disable_max_rows()

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory=False)

v8_pisa = pisa_df[
    (pisa_df["ESCS"].notna()) &
    (pisa_df["PV1MATH"].notna()) &
    (pisa_df["ANXMAT"].notna()) &
    (pisa_df["CNT"].notna()) &
    (pisa_df["ST004D01T"].isin([1, 2]))
].copy()

v8_pv_cols = [f"PV{i}MATH" for i in range(1, 11)]
v8_available_pv = [col for col in v8_pv_cols if col in v8_pisa.columns]
v8_pisa["Math_Score"] = v8_pisa[v8_available_pv].mean(axis=1)
v8_pisa["Gender"] = v8_pisa["ST004D01T"].map({1: "Female", 2: "Male"})

escs_terciles = v8_pisa["ESCS"].quantile([0.33, 0.67]).values
v8_pisa["SES_Level"] = pd.cut(
    v8_pisa["ESCS"],
    bins=[-np.inf, escs_terciles[0], escs_terciles[1], np.inf],
    labels=["Low SES", "Medium SES", "High SES"]
)

v8_country_gender_agg = v8_pisa.groupby(["CNT", "Gender"]).agg(
    Mean_ESCS=("ESCS", "mean"),
    Mean_Math=("Math_Score", "mean"),
    n=("CNT", "size")
).reset_index()

v8_country_gender_agg["OECD_Status"] = v8_country_gender_agg["CNT"].apply(
    lambda x: "OECD" if x in OECD_COUNTRIES else "Non-OECD"
)
v8_country_gender_agg["Gender_OECD"] = v8_country_gender_agg["Gender"] + " " + v8_country_gender_agg["OECD_Status"]

v8_right_df = v8_pisa[["CNT", "Gender", "SES_Level", "ANXMAT"]].dropna().copy()

v8_brush_select = alt.selection_interval(name="brush_select")

v8_ses_order = ["Low SES", "Medium SES", "High SES"]
v8_gender_colors = ["#E91E63", "#1976D2"]
v8_gender_oecd_domain = ["Female OECD", "Female Non-OECD", "Male OECD", "Male Non-OECD"]
v8_gender_oecd_colors = ["#D81B60", "#FF6F00", "#1565C0", "#00897B"]

v8_left_chart = alt.Chart(v8_country_gender_agg).mark_circle(size=80, cursor="crosshair").encode(
    x=alt.X("Mean_ESCS:Q", title="Mean SES (ESCS)",
            scale=alt.Scale(domain=[-2.5, 1.0])),
    y=alt.Y("Mean_Math:Q", title="Mean Math Score",
            scale=alt.Scale(domain=[300, 600])),
    color=alt.Color("Gender_OECD:N",
                   scale=alt.Scale(domain=v8_gender_oecd_domain, range=v8_gender_oecd_colors),
                   legend=alt.Legend(title="Gender & OECD", orient="top")),
    opacity=alt.condition(v8_brush_select, alt.value(1), alt.value(0.3)),
    tooltip=[
        alt.Tooltip("CNT:N", title="Country"),
        alt.Tooltip("Gender:N"),
        alt.Tooltip("OECD_Status:N", title="OECD Status"),
        alt.Tooltip("Mean_ESCS:Q", title="Mean SES", format=".2f"),
        alt.Tooltip("Mean_Math:Q", title="Mean Math", format=".0f"),
        alt.Tooltip("n:Q", title="Students", format=",d")
    ]
).add_params(v8_brush_select).properties(
    title={"text": "PISA: Country-Level SES vs Math",
           "subtitle": "Drag to select countries and filter right chart",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width=320, height=300
)

v8_right_chart = (
    alt.Chart(v8_right_df)
    .transform_filter(v8_brush_select)
    .transform_aggregate(
        Mean_Anxiety="mean(ANXMAT)",
        Count="count()",
        groupby=["SES_Level", "Gender"]
    )
    .mark_bar()
    .encode(
        x=alt.X("SES_Level:N", title="SES Level",
                sort=v8_ses_order,
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Mean_Anxiety:Q", title="Mean Math Anxiety",
                scale=alt.Scale(domain=[-0.5, 0.5])),
        color=alt.Color("Gender:N", title="Gender",
                       scale=alt.Scale(domain=["Female", "Male"], range=v8_gender_colors),
                       legend=alt.Legend(orient="top")),
        xOffset=alt.XOffset("Gender:N", sort=["Female", "Male"]),
        tooltip=[
            alt.Tooltip("SES_Level:N", title="SES Level"),
            alt.Tooltip("Gender:N", title="Gender"),
            alt.Tooltip("Mean_Anxiety:Q", title="Mean Math Anxiety", format=".3f"),
            alt.Tooltip("Count:Q", title="Students", format=",d")
        ]
    )
    .properties(
        title={"text": "Math Anxiety by SES Level and Gender",
               "subtitle": "Filtered by country selection from left chart",
               "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
        width=400, height=300
    )
)

viz8 = alt.hconcat(v8_left_chart, v8_right_chart).resolve_scale(color="independent")
save_chart(viz8, "combined_efficacy_comparison.json")
