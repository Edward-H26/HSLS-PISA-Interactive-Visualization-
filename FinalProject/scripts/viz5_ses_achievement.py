import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart, CONTINENT_MAP

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory = False)
hsls_df = pd.read_csv(DATA_DIR / "hsls_subset.csv", low_memory = False)

v5_pisa = pisa_df[["CNT", "ESCS", "MATHEFF", "MATHPERS", "ST004D01T"]].copy()
v5_pisa = v5_pisa[(v5_pisa["ESCS"].notna()) &
                   (v5_pisa["MATHEFF"].notna()) &
                   (v5_pisa["MATHPERS"].notna()) &
                   (v5_pisa["ST004D01T"].isin([1, 2]))]
v5_pisa = v5_pisa.assign(source = "PISA")
v5_pisa["continent"] = v5_pisa["CNT"].map(CONTINENT_MAP).fillna("Other")

v5_hsls = hsls_df[["X1SES", "X1MTHEFF", "X1STU30OCC_STEM1", "X1SEX"]].copy()
v5_hsls = v5_hsls[(v5_hsls["X1SES"] > -1) &
                   (v5_hsls["X1MTHEFF"] > -1) &
                   (v5_hsls["X1STU30OCC_STEM1"] >= 0) &
                   (v5_hsls["X1SEX"].isin([1, 2]))]
v5_hsls = v5_hsls.assign(CNT = "USA", continent = "North America", source = "HSLS")

v5_pisa_base = v5_pisa.rename(columns = {"ESCS": "escs", "MATHEFF": "matheff"})[["continent", "escs", "matheff"]].copy()
v5_pisa_base = v5_pisa_base.dropna(subset = ["escs", "matheff", "continent"])
v5_pisa_base["z_escs"] = (v5_pisa_base["escs"] - v5_pisa_base["escs"].mean()) / v5_pisa_base["escs"].std(ddof = 0)
v5_pisa_base["z_matheff"] = (v5_pisa_base["matheff"] - v5_pisa_base["matheff"].mean()) / v5_pisa_base["matheff"].std(ddof = 0)

v5_continent_agg = (
    v5_pisa_base.groupby("continent")
    .agg(avg_escs = ("z_escs", "mean"), avg_matheff = ("z_matheff", "mean"), n = ("z_escs", "size"))
    .reset_index()
)

v5_pisa_students = (
    v5_pisa.rename(columns = {"ST004D01T": "gender"})
    .assign(
        continent = lambda d: d["CNT"].map(CONTINENT_MAP).fillna("Other"),
        source = "PISA",
        gender = lambda d: d["gender"].map({1: "Female", 2: "Male"}),
        stem_interest = lambda d: d["MATHPERS"],
    )
    [["continent", "gender", "stem_interest", "source"]]
    .dropna(subset = ["stem_interest", "gender", "continent"])
)
v5_hsls_students = (
    v5_hsls.rename(columns = {"X1SEX": "gender"})
    .assign(
        source = "HSLS",
        gender = lambda d: d["gender"].map({1: "Male", 2: "Female"}),
        stem_interest = lambda d: d["X1STU30OCC_STEM1"],
    )
    [["continent", "gender", "stem_interest", "source"]]
    .dropna(subset = ["stem_interest", "gender", "continent"])
)
v5_hsls_students = v5_hsls_students[v5_hsls_students["stem_interest"].isin([0, 1, 2, 3, 4, 5, 6])]
v5_students = pd.concat([v5_pisa_students, v5_hsls_students], ignore_index = True)

v5_sampled_students = v5_students.groupby(["continent", "gender"]).apply(
    lambda x: x.sample(n = min(len(x), 2000), random_state = 42)
).reset_index(drop = True)

v5_continent_select = alt.selection_point(
    fields = ["continent"],
    name = "continent_select",
    empty = True
)

v5_left_chart = (
    alt.Chart(v5_continent_agg)
    .mark_circle(cursor = "pointer")
    .encode(
        x = alt.X("avg_escs:Q", title = "Mean SES (z within source)"),
        y = alt.Y("avg_matheff:Q", title = "Mean Math Self-Efficacy (z within source)"),
        size = alt.Size("n:Q", scale = alt.Scale(range = [60, 500]), legend = None),
        color = alt.Color("continent:N", title = "Continent/Region"),
        opacity = alt.condition(v5_continent_select, alt.value(1), alt.value(0.4)),
        tooltip = [
            alt.Tooltip("continent:N", title = "Continent"),
            alt.Tooltip("avg_escs:Q", title = "Mean SES", format = ".2f"),
            alt.Tooltip("avg_matheff:Q", title = "Mean Math Efficacy", format = ".2f"),
            alt.Tooltip("n:Q", title = "Sample Size", format = ",d")
        ],
    )
    .add_params(v5_continent_select)
    .properties(
        name = "view_1",
        title = {"text": "Socioeconomic Status and Mathematics Self-Efficacy", "subtitle": "Standardized mean scores by geographic region",
                "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
        width = 280, height = 240
    )
)

v5_right_chart = (
    alt.Chart(v5_sampled_students)
    .transform_filter(v5_continent_select)
    .transform_density(
        density = "stem_interest",
        groupby = ["gender"],
        as_ = ["stem_interest", "density"],
    )
    .mark_area(opacity = 0.5)
    .encode(
        x = alt.X("stem_interest:Q", title = "STEM Interest Index"),
        y = alt.Y("density:Q", title = "Density"),
        color = alt.Color("gender:N", title = "Gender", scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"])),
    )
    .properties(
        title = {"text": "Distribution of STEM Interest by Gender", "subtitle": "Density estimates for selected geographic region",
                "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
        width = 280, height = 240
    )
)

viz5 = alt.hconcat(v5_left_chart, v5_right_chart).resolve_scale(color = "independent").configure_view(
    stroke = None,
    fill = None
).properties(
    background = "transparent"
)
save_chart(viz5, "combined_ses_achievement.json")
