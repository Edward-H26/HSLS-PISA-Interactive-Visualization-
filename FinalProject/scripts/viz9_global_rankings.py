import pandas as pd
import altair as alt
import numpy as np
from config import DATA_DIR, save_chart

alt.data_transformers.disable_max_rows()

pisa_cols = ["BELONG", "PV1MATH", "PV1READ", "PV1SCIE", "MATHEFF", "MATHPERS", "IMMIG"]
pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", usecols=pisa_cols, low_memory=False)

v9_data = pisa_df[
    (pisa_df["BELONG"].notna()) &
    (pisa_df["PV1MATH"].notna()) &
    (pisa_df["PV1READ"].notna()) &
    (pisa_df["PV1SCIE"].notna()) &
    (pisa_df["MATHEFF"].notna()) &
    (pisa_df["MATHPERS"].notna()) &
    (pisa_df["IMMIG"].isin([1, 2, 3, 1.0, 2.0, 3.0]))
].copy()

belong_terciles = v9_data["BELONG"].quantile([0.33, 0.67]).values
v9_data["belong_level"] = pd.cut(
    v9_data["BELONG"],
    bins=[-np.inf, belong_terciles[0], belong_terciles[1], np.inf],
    labels=["Low Belonging", "Medium Belonging", "High Belonging"]
)

v9_immig_map = {1: "Native", 1.0: "Native", 2: "Second-Gen", 2.0: "Second-Gen", 3: "First-Gen", 3.0: "First-Gen"}
v9_data["immig_status"] = v9_data["IMMIG"].map(v9_immig_map)

v9_belong_order = ["Low Belonging", "Medium Belonging", "High Belonging"]
v9_domain_colors = ["#E91E63", "#00E676", "#2979FF"]
v9_immig_colors = ["#1E88E5", "#FF0000", "#FFD700"]

v9_math = v9_data.groupby("belong_level", observed=True)["PV1MATH"].mean().reset_index()
v9_math["Domain"] = "MATH"
v9_math.columns = ["belong_level", "mean_score", "Domain"]

v9_read = v9_data.groupby("belong_level", observed=True)["PV1READ"].mean().reset_index()
v9_read["Domain"] = "READ"
v9_read.columns = ["belong_level", "mean_score", "Domain"]

v9_scie = v9_data.groupby("belong_level", observed=True)["PV1SCIE"].mean().reset_index()
v9_scie["Domain"] = "SCIE"
v9_scie.columns = ["belong_level", "mean_score", "Domain"]

v9_left_df = pd.concat([v9_math, v9_read, v9_scie], ignore_index=True)

v9_right_df = v9_data[["belong_level", "immig_status", "MATHEFF", "MATHPERS"]].dropna().sample(n=6000, random_state=42)

v9_belong_selection = alt.selection_point(fields=["belong_level"], name="v9_belong_select")

v9_left_chart = alt.Chart(v9_left_df).mark_line(
    point=alt.OverlayMarkDef(filled=True, size=80),
    strokeWidth=4,
    cursor="pointer"
).encode(
    x=alt.X("Domain:N", title="Domain",
            sort=["MATH", "READ", "SCIE"],
            axis=alt.Axis(labelAngle=0, labelFontSize=11)),
    y=alt.Y("mean_score:Q", title="Mean Score",
            scale=alt.Scale(domain=[425, 490])),
    color=alt.Color("belong_level:N", title="Belonging Level",
                   scale=alt.Scale(domain=v9_belong_order, range=v9_domain_colors),
                   legend=alt.Legend(orient="top")),
    opacity=alt.condition(v9_belong_selection, alt.value(1), alt.value(0.3)),
    tooltip=[
        alt.Tooltip("Domain:N", title="Domain"),
        alt.Tooltip("belong_level:N", title="Belonging Level"),
        alt.Tooltip("mean_score:Q", title="Mean Score", format=".1f")
    ]
).add_params(v9_belong_selection).properties(
    title={"text": "Academic Scores by Domain",
           "subtitle": "Click line to filter right plot",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width=450, height=400
)

v9_right_scatter = (
    alt.Chart(v9_right_df)
    .transform_filter(v9_belong_selection)
    .transform_sample(2000)
    .mark_circle(size=40)
    .encode(
        x=alt.X("MATHEFF:Q", title="Math Self-Efficacy",
                scale=alt.Scale(domain=[-4, 4])),
        y=alt.Y("MATHPERS:Q", title="Math Persistence",
                scale=alt.Scale(domain=[-4, 4])),
        color=alt.Color("immig_status:N", title="Immigration Status",
                       scale=alt.Scale(domain=["Native", "Second-Gen", "First-Gen"], range=v9_immig_colors),
                       legend=alt.Legend(orient="top")),
        opacity=alt.Opacity("immig_status:N",
                           scale=alt.Scale(domain=["Native", "Second-Gen", "First-Gen"], range=[0.4, 0.9, 0.9]),
                           legend=None),
        tooltip=[
            alt.Tooltip("immig_status:N", title="Immigration"),
            alt.Tooltip("MATHEFF:Q", title="Self-Efficacy", format=".2f"),
            alt.Tooltip("MATHPERS:Q", title="Persistence", format=".2f")
        ]
    )
)

v9_right_regression = (
    alt.Chart(v9_right_df)
    .transform_filter(v9_belong_selection)
    .transform_regression("MATHEFF", "MATHPERS", groupby=["immig_status"])
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("MATHEFF:Q"),
        y=alt.Y("MATHPERS:Q"),
        color=alt.Color("immig_status:N", scale=alt.Scale(domain=["Native", "Second-Gen", "First-Gen"], range=v9_immig_colors))
    )
)

v9_right_chart = alt.layer(v9_right_scatter, v9_right_regression).properties(
    title={"text": "Self-Efficacy vs Persistence by Immigration Status",
           "subtitle": "Filtered by school belonging selection",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width=400, height=400
)

viz9 = alt.hconcat(v9_left_chart, v9_right_chart).resolve_scale(color="independent")
save_chart(viz9, "combined_gender_stem.json")
