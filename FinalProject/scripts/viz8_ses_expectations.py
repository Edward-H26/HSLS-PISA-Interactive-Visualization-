import pandas as pd
import altair as alt
import numpy as np
from config import DATA_DIR, save_chart, CONTINENT_MAP

alt.data_transformers.disable_max_rows()

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory=False)

v8_pisa = pisa_df[
    (pisa_df["ESCS"].notna()) &
    (pisa_df["PV1MATH"].notna()) &
    (pisa_df["PV1SCIE"].notna()) &
    (pisa_df["PV1READ"].notna()) &
    (pisa_df["CNT"].notna()) &
    (pisa_df["ST004D01T"].isin([1, 2]))
].copy()

v8_math_cols = [f"PV{i}MATH" for i in range(1, 11)]
v8_scie_cols = [f"PV{i}SCIE" for i in range(1, 11)]
v8_read_cols = [f"PV{i}READ" for i in range(1, 11)]
v8_available_math = [col for col in v8_math_cols if col in v8_pisa.columns]
v8_available_scie = [col for col in v8_scie_cols if col in v8_pisa.columns]
v8_available_read = [col for col in v8_read_cols if col in v8_pisa.columns]

v8_pisa["Math_Score"] = v8_pisa[v8_available_math].mean(axis=1)
v8_pisa["Science_Score"] = v8_pisa[v8_available_scie].mean(axis=1)
v8_pisa["Reading_Score"] = v8_pisa[v8_available_read].mean(axis=1)
v8_pisa["Gender"] = v8_pisa["ST004D01T"].map({1: "Female", 2: "Male"})
v8_pisa["Continent"] = v8_pisa["CNT"].map(CONTINENT_MAP).fillna("Other")

v8_continent_agg = v8_pisa.groupby(["Continent"]).agg(
    Mean_Math=("Math_Score", "mean"),
    Mean_Science=("Science_Score", "mean"),
    Mean_Reading=("Reading_Score", "mean"),
    n=("Continent", "size")
).reset_index()

v8_continent_gender_agg = v8_pisa.groupby(["Continent", "Gender"]).agg(
    Mean_Math=("Math_Score", "mean"),
    Mean_Science=("Science_Score", "mean"),
    Mean_Reading=("Reading_Score", "mean"),
    n=("Continent", "size")
).reset_index()

v8_gender_subject_long = v8_continent_gender_agg.melt(
    id_vars=["Continent", "Gender", "n"],
    value_vars=["Mean_Math", "Mean_Science", "Mean_Reading"],
    var_name="Subject",
    value_name="Score"
)
v8_gender_subject_long["Subject"] = v8_gender_subject_long["Subject"].map({"Mean_Math": "Math", "Mean_Science": "Science", "Mean_Reading": "Reading"})
v8_gender_subject_long["Category"] = v8_gender_subject_long["Gender"] + " " + v8_gender_subject_long["Subject"]

v8_continent_select = alt.selection_point(fields=["Continent"], name="continent_select", empty="all")

v8_continent_order = ["Europe", "Asia", "North America", "South America", "Oceania", "Africa", "Other"]
v8_continent_colors = ["#4CAF50", "#FF9800", "#2196F3", "#9C27B0", "#00BCD4", "#FF5722", "#607D8B"]
v8_subject_colors = ["#E91E63", "#00BCD4", "#4CAF50"]
v8_category_order = ["Female Math", "Female Science", "Female Reading", "Male Math", "Male Science", "Male Reading"]

v8_left_chart = (
    alt.Chart(v8_continent_agg)
    .mark_bar(cursor="pointer", cornerRadiusTopRight=4, cornerRadiusTopLeft=4)
    .encode(
        x=alt.X("Continent:N", title="Continent", sort=v8_continent_order,
                axis=alt.Axis(labelAngle=-45, labelFontSize=10)),
        y=alt.Y("Mean_Math:Q", title="Mean Math Score",
                scale=alt.Scale(domain=[350, 550], clamp=True)),
        color=alt.Color("Continent:N",
                       scale=alt.Scale(domain=v8_continent_order, range=v8_continent_colors),
                       legend=alt.Legend(title="Continent", orient="top", columns=4)),
        opacity=alt.condition(v8_continent_select, alt.value(1), alt.value(0.4)),
        tooltip=[
            alt.Tooltip("Continent:N", title="Continent"),
            alt.Tooltip("Mean_Math:Q", title="Mean Math Score", format=".0f"),
            alt.Tooltip("Mean_Science:Q", title="Mean Science Score", format=".0f"),
            alt.Tooltip("n:Q", title="Students", format=",d")
        ]
    )
    .add_params(v8_continent_select)
    .properties(
        name="view_1",
        title={"text": "Average Math Scores by Continent",
               "subtitle": "Click a continent to filter the chart on right",
               "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
        width=350, height=300
    )
)

v8_right_chart = (
    alt.Chart(v8_gender_subject_long)
    .transform_filter(v8_continent_select)
    .transform_aggregate(
        Score="mean(Score)",
        Total_Students="sum(n)",
        groupby=["Category", "Gender", "Subject"]
    )
    .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
    .encode(
        y=alt.Y("Category:N", title="Gender × Subject",
                sort=v8_category_order,
                axis=alt.Axis(labelAngle=0, labelFontSize=11)),
        x=alt.X("Score:Q", title="Mean Score",
                scale=alt.Scale(domain=[400, 520], clamp=True)),
        color=alt.Color("Subject:N", title="Subject",
                       scale=alt.Scale(domain=["Math", "Science", "Reading"], range=v8_subject_colors),
                       legend=alt.Legend(orient="top", direction="horizontal")),
        tooltip=[
            alt.Tooltip("Category:N", title="Category"),
            alt.Tooltip("Score:Q", title="Mean Score", format=".0f"),
            alt.Tooltip("Total_Students:Q", title="Students", format=",d")
        ]
    )
    .properties(
        title={"text": "Math, Science & Reading by Gender",
               "subtitle": "Showing average across selected region(s)",
               "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
        width=300, height=280
    )
)

viz8 = alt.hconcat(v8_left_chart, v8_right_chart).resolve_scale(color="independent")
save_chart(viz8, "combined_efficacy_comparison.json")
