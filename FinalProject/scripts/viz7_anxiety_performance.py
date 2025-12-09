import pandas as pd
import altair as alt
import numpy as np
from config import DATA_DIR, save_chart

alt.data_transformers.disable_max_rows()

pisa_cols = ["HISCED", "ESCS", "ANXMAT", "BELONG", "ST004D01T"]
pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", usecols=pisa_cols, low_memory=False)

v7_parent_edu_map = {
    0: "No Education", 0.0: "No Education",
    1: "Primary", 1.0: "Primary", 2: "Primary", 2.0: "Primary",
    3: "Lower Secondary", 3.0: "Lower Secondary", 4: "Lower Secondary", 4.0: "Lower Secondary",
    5: "Upper Secondary", 5.0: "Upper Secondary", 6: "Upper Secondary", 6.0: "Upper Secondary",
    7: "Post-Secondary", 7.0: "Post-Secondary", 8: "Post-Secondary", 8.0: "Post-Secondary",
    9: "Bachelor's+", 9.0: "Bachelor's+", 10: "Bachelor's+", 10.0: "Bachelor's+"
}

v7_gender_map = {1: "Female", 1.0: "Female", 2: "Male", 2.0: "Male"}

v7_data = pisa_df[
    (pisa_df["HISCED"].notna()) &
    (pisa_df["ESCS"].notna()) &
    (pisa_df["ANXMAT"].notna()) &
    (pisa_df["BELONG"].notna()) &
    (pisa_df["ST004D01T"].isin([1, 2, 1.0, 2.0]))
].copy()

v7_data["parent_education"] = v7_data["HISCED"].map(v7_parent_edu_map).fillna("Unknown")
v7_data["gender"] = v7_data["ST004D01T"].map(v7_gender_map)

escs_terciles = v7_data["ESCS"].quantile([0.33, 0.67]).values
v7_data["ses_level"] = pd.cut(
    v7_data["ESCS"],
    bins=[-np.inf, escs_terciles[0], escs_terciles[1], np.inf],
    labels=["Low SES", "Medium SES", "High SES"]
)

v7_parent_edu_order = ["No Education", "Primary", "Lower Secondary", "Upper Secondary", "Post-Secondary", "Bachelor's+"]
v7_ses_order = ["Low SES", "Medium SES", "High SES"]
v7_gender_colors = ["#E91E63", "#1976D2"]

v7_heatmap_df = (
    v7_data[v7_data["parent_education"] != "Unknown"]
    .groupby(["parent_education", "ses_level"], observed=True)
    .agg(
        avg_anxiety=("ANXMAT", "mean"),
        student_count=("ANXMAT", "count")
    )
    .reset_index()
)

v7_scatter_df = v7_data[["parent_education", "gender", "BELONG", "ANXMAT"]].dropna().copy()
v7_scatter_df = v7_scatter_df[v7_scatter_df["parent_education"] != "Unknown"]
v7_scatter_df = v7_scatter_df.sample(n=min(2000, len(v7_scatter_df)), random_state=42)

v7_edu_selection = alt.selection_point(fields=["parent_education"], name="v7_edu_select")

v7_left_chart = (
    alt.Chart(v7_heatmap_df)
    .mark_rect(cursor="pointer")
    .encode(
        x=alt.X("parent_education:N", title="Parental Education Level",
                sort=v7_parent_edu_order,
                axis=alt.Axis(labelAngle=-45, labelFontSize=10)),
        y=alt.Y("ses_level:N", title="SES Level",
                sort=v7_ses_order),
        color=alt.Color("avg_anxiety:Q", title="Mean Math Anxiety",
                       scale=alt.Scale(scheme="redblue", domain=[-0.5, 0.5], reverse=True)),
        opacity=alt.condition(v7_edu_selection, alt.value(1), alt.value(0.4)),
        tooltip=[
            alt.Tooltip("parent_education:N", title="Parent Education"),
            alt.Tooltip("ses_level:N", title="SES Level"),
            alt.Tooltip("avg_anxiety:Q", title="Mean Anxiety", format=".3f"),
            alt.Tooltip("student_count:Q", title="Students", format=",d")
        ]
    )
    .add_params(v7_edu_selection)
    .properties(
        title={"text": "Math Anxiety by Parental Education & SES",
               "subtitle": "Click a parental education level to filter right plot",
               "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
        width=450, height=400
    )
)

v7_right_chart = (
    alt.Chart(v7_scatter_df)
    .transform_filter(v7_edu_selection)
    .mark_circle(size=30, opacity=0.5)
    .encode(
        x=alt.X("BELONG:Q", title="School Belonging Score",
                scale=alt.Scale(domain=[-4, 4])),
        y=alt.Y("ANXMAT:Q", title="Math Anxiety Score",
                scale=alt.Scale(domain=[-3, 3])),
        color=alt.Color("gender:N", title="Gender",
                       scale=alt.Scale(domain=["Female", "Male"], range=v7_gender_colors),
                       legend=alt.Legend(orient="top")),
        tooltip=[
            alt.Tooltip("gender:N", title="Gender"),
            alt.Tooltip("BELONG:Q", title="School Belonging", format=".2f"),
            alt.Tooltip("ANXMAT:Q", title="Math Anxiety", format=".2f")
        ]
    )
    .properties(
        title={"text": "School Belonging vs Math Anxiety by Gender",
               "subtitle": "Filtered by parental education selection",
               "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
        width=400, height=400
    )
)

viz7 = alt.hconcat(v7_left_chart, v7_right_chart).resolve_scale(color="independent")
save_chart(viz7, "pisa_anxiety_performance_heatmap.json")
