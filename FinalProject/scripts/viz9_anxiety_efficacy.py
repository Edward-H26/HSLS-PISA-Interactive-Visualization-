import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart, OECD_COUNTRIES

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory = False)
hsls_df = pd.read_csv(DATA_DIR / "hsls_subset.csv", low_memory = False)

v9_pisa_cols = ["CNT", "ST004D01T", "ANXMAT"]
v9_pisa = pisa_df[v9_pisa_cols].copy()
v9_pisa = v9_pisa[(v9_pisa["ST004D01T"].isin([1, 2])) & (v9_pisa["ANXMAT"].notna())]
v9_pisa["Gender"] = v9_pisa["ST004D01T"].map({1: "Female", 2: "Male"})

v9_country_gender_agg = v9_pisa.groupby(["CNT", "Gender"]).agg(
    Mean_Anxiety = ("ANXMAT", "mean"),
    n = ("ANXMAT", "count")
).reset_index()

v9_country_gender_agg["OECD_Status"] = v9_country_gender_agg["CNT"].apply(
    lambda x: "OECD" if x in OECD_COUNTRIES else "Non-OECD"
)

v9_country_means = v9_country_gender_agg.groupby("CNT")["Mean_Anxiety"].mean().reset_index()
v9_country_means = v9_country_means.sort_values("Mean_Anxiety", ascending = False)
v9_top_30_countries = v9_country_means.head(30)["CNT"].tolist()

v9_dumbbell_data = v9_country_gender_agg[v9_country_gender_agg["CNT"].isin(v9_top_30_countries)]

v9_lines_data = v9_dumbbell_data.pivot(index = ["CNT", "OECD_Status"], columns = "Gender", values = "Mean_Anxiety").reset_index()
v9_lines_data.columns.name = None
v9_lines_data = v9_lines_data.rename(columns = {"Female": "Female_Anxiety", "Male": "Male_Anxiety"})

v9_lines = alt.Chart(v9_lines_data).mark_rule(strokeWidth = 1.5, opacity = 0.6).encode(
    y = alt.Y("CNT:N", title = "Country", sort = alt.EncodingSortField(field = "Female_Anxiety", order = "descending")),
    x = alt.X("Female_Anxiety:Q", title = "Mathematics Anxiety", scale = alt.Scale(domain = [-0.6, 0.8])),
    x2 = alt.X2("Male_Anxiety:Q"),
    color = alt.Color("OECD_Status:N", scale = alt.Scale(domain = ["OECD", "Non-OECD"], range = ["#1976D2", "#E91E63"]), title = "OECD Status")
)

v9_points = alt.Chart(v9_dumbbell_data).mark_point(size = 100, filled = True).encode(
    y = alt.Y("CNT:N", title = "Country", sort = alt.EncodingSortField(field = "Mean_Anxiety", order = "descending")),
    x = alt.X("Mean_Anxiety:Q", title = "Mathematics Anxiety", scale = alt.Scale(domain = [-0.6, 0.8])),
    color = alt.Color("OECD_Status:N", scale = alt.Scale(domain = ["OECD", "Non-OECD"], range = ["#1976D2", "#E91E63"]), title = "OECD Status"),
    shape = alt.Shape("Gender:N", scale = alt.Scale(domain = ["Female", "Male"], range = ["circle", "square"]), title = "Gender"),
    tooltip = [
        alt.Tooltip("CNT:N", title = "Country"),
        alt.Tooltip("Gender:N", title = "Gender"),
        alt.Tooltip("Mean_Anxiety:Q", title = "Math Anxiety", format = ".3f"),
        alt.Tooltip("OECD_Status:N", title = "OECD Status"),
        alt.Tooltip("n:Q", title = "Sample Size", format = ",d")
    ]
)

v9_left_chart = (v9_lines + v9_points).properties(
    title = {"text": "PISA: Math Anxiety by Country and Gender", "subtitle": "Dumbbell chart showing gender gap within countries",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 500, height = 500
)

v9_hsls_cols = ["X1SEX", "X1MTHEFF"]
v9_hsls = hsls_df[v9_hsls_cols].copy()
v9_hsls = v9_hsls[(v9_hsls["X1SEX"].isin([1, 2])) & (v9_hsls["X1MTHEFF"].notna())]
v9_hsls["Gender"] = v9_hsls["X1SEX"].map({1: "Male", 2: "Female"})

v9_hsls_sampled = v9_hsls.groupby("Gender", group_keys = False).apply(
    lambda x: x.sample(min(len(x), 5000), random_state = 42)
).reset_index(drop = True)

v9_right_chart = alt.Chart(v9_hsls_sampled).transform_density(
    density = "X1MTHEFF",
    groupby = ["Gender"],
    as_ = ["X1MTHEFF", "density"]
).mark_area(opacity = 0.5).encode(
    x = alt.X("X1MTHEFF:Q", title = "Math Self-Efficacy"),
    y = alt.Y("density:Q", title = "Density"),
    color = alt.Color("Gender:N", scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]), title = "Gender"),
    tooltip = [
        alt.Tooltip("Gender:N", title = "Gender"),
        alt.Tooltip("X1MTHEFF:Q", title = "Math Efficacy", format = ".2f"),
        alt.Tooltip("density:Q", title = "Density", format = ".3f")
    ]
).properties(
    title = {"text": "HSLS: Math Self-Efficacy Distribution", "subtitle": "Density plot by gender",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 400, height = 500
)

viz9 = alt.hconcat(v9_left_chart, v9_right_chart).resolve_scale(color = "independent")
save_chart(viz9, "combined_parent_education.json")
