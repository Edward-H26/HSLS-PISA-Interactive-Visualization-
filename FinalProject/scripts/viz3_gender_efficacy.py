import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart, COUNTRY_NAME_MAP, CONTINENT_MAP

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory = False)

v3_data = pisa_df[(pisa_df["MATHEFF"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2])) &
                   (pisa_df["CNT"].notna())].copy()
v3_data["Gender"] = v3_data["ST004D01T"].map({1: "Female", 2: "Male"})
v3_data["Country"] = v3_data["CNT"].map(COUNTRY_NAME_MAP).fillna(v3_data["CNT"])
v3_data["Continent"] = v3_data["CNT"].map(CONTINENT_MAP).fillna("Other")

v3_country_gender = v3_data.groupby(["Country", "Gender", "Continent"]).agg(
    Efficacy = ("MATHEFF", "mean"),
    Math_Score = ("PV1MATH", "mean"),
    Count = ("MATHEFF", "count")
).reset_index()

v3_eff_pivot = v3_country_gender.pivot(index = ["Country", "Continent"], columns = "Gender", values = "Efficacy").reset_index()
v3_eff_pivot.columns = ["Country", "Continent", "Female_Eff", "Male_Eff"]
v3_eff_pivot["Efficacy_Gap"] = v3_eff_pivot["Male_Eff"] - v3_eff_pivot["Female_Eff"]

v3_score_pivot = v3_country_gender.pivot(index = "Country", columns = "Gender", values = "Math_Score").reset_index()
v3_score_pivot.columns = ["Country", "Female_Score", "Male_Score"]
v3_score_pivot["Score_Gap"] = v3_score_pivot["Male_Score"] - v3_score_pivot["Female_Score"]

v3_count_pivot = v3_country_gender.pivot(index = "Country", columns = "Gender", values = "Count").reset_index()
v3_count_pivot.columns = ["Country", "Female_N", "Male_N"]

v3_gap_df = v3_eff_pivot.merge(v3_score_pivot, on = "Country").merge(v3_count_pivot, on = "Country")
v3_gap_df["Total_N"] = v3_gap_df["Female_N"] + v3_gap_df["Male_N"]
v3_gap_df = v3_gap_df.dropna()

v3_continent_order = ["Europe", "Asia", "North America", "South America", "Oceania", "Africa", "Other"]
v3_continent_colors = ["#4CAF50", "#FF9800", "#2196F3", "#9C27B0", "#00BCD4", "#FF5722", "#607D8B"]

v3_country_select = alt.selection_point(fields = ["Country"], name = "country_select")

v3_left_chart = alt.Chart(v3_gap_df).mark_circle(
    stroke = "#0f172a", strokeWidth = 0.8, cursor = "pointer"
).encode(
    x = alt.X("Efficacy_Gap:Q", title = "Self-Efficacy Gap (Male - Female)",
             scale = alt.Scale(zero = False),
             axis = alt.Axis(labelFontSize = 11, titleFontSize = 12, grid = True, gridOpacity = 0.3)),
    y = alt.Y("Score_Gap:Q", title = "Math Score Gap (Male - Female)",
             scale = alt.Scale(zero = False),
             axis = alt.Axis(labelFontSize = 11, titleFontSize = 12, grid = True, gridOpacity = 0.3)),
    color = alt.Color("Continent:N", title = "Continent",
                     scale = alt.Scale(domain = v3_continent_order, range = v3_continent_colors),
                     legend = alt.Legend(orient = "top", titleFontSize = 11, labelFontSize = 10,
                                        direction = "horizontal", columns = 4)),
    size = alt.Size("Total_N:Q", title = "Sample Size",
                   scale = alt.Scale(range = [50, 400]), legend = None),
    opacity = alt.condition(v3_country_select, alt.value(1), alt.value(0.4)),
    tooltip = [
        alt.Tooltip("Country:N", title = "Country"),
        alt.Tooltip("Continent:N", title = "Continent"),
        alt.Tooltip("Efficacy_Gap:Q", title = "Efficacy Gap (M-F)", format = ".3f"),
        alt.Tooltip("Score_Gap:Q", title = "Score Gap (M-F)", format = ".1f"),
        alt.Tooltip("Total_N:Q", title = "Sample Size", format = ",d")
    ]
).add_params(v3_country_select).properties(
    width = 450, height = 420,
    title = alt.TitleParams(
        text = "Gender Gaps in Math Confidence vs Achievement",
        subtitle = "Each point is a country. Click to see gender breakdown on right.",
        fontSize = 15, subtitleFontSize = 11,
        font = "Roboto, sans-serif", anchor = "middle", fontWeight = 700,
        color = "#FFFFFF", subtitleColor = "#E0E0E0",
        offset = 10, subtitlePadding = 4
    )
)

v3_eff_long = v3_gap_df[["Country", "Female_Eff", "Male_Eff"]].melt(
    id_vars = "Country", var_name = "Gender", value_name = "Value"
)
v3_eff_long["Gender"] = v3_eff_long["Gender"].str.replace("_Eff", "")
v3_eff_long["Metric"] = "Self-Efficacy"

v3_score_long = v3_gap_df[["Country", "Female_Score", "Male_Score"]].melt(
    id_vars = "Country", var_name = "Gender", value_name = "Value"
)
v3_score_long["Gender"] = v3_score_long["Gender"].str.replace("_Score", "")
v3_score_long["Metric"] = "Math Score"

v3_detail_df = pd.concat([v3_eff_long, v3_score_long], ignore_index = True)

v3_right_chart = alt.Chart(v3_detail_df).transform_filter(v3_country_select).mark_line(
    point = alt.OverlayMarkDef(filled = True, size = 100),
    strokeWidth = 2.5
).encode(
    x = alt.X("Metric:N", title = "Metric", sort = ["Self-Efficacy", "Math Score"],
             axis = alt.Axis(labelFontSize = 12, labelAngle = 0, labelPadding = 8)),
    y = alt.Y("Value:Q", title = "Value",
             axis = alt.Axis(labelFontSize = 11, titleFontSize = 12, grid = True, gridOpacity = 0.3)),
    color = alt.Color("Gender:N", title = "Gender",
                     scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]),
                     legend = alt.Legend(orient = "top", titleFontSize = 11, labelFontSize = 10,
                                        direction = "horizontal", symbolSize = 80)),
    tooltip = [
        alt.Tooltip("Metric:N", title = "Metric"),
        alt.Tooltip("Gender:N", title = "Gender"),
        alt.Tooltip("Value:Q", title = "Value", format = ".2f")
    ]
).properties(
    width = 380, height = 420,
    title = alt.TitleParams(
        text = "Gender Comparison for Selected Country",
        subtitle = "Lines connect each gender's Self-Efficacy to Math Score",
        fontSize = 15, subtitleFontSize = 11,
        font = "Roboto, sans-serif", anchor = "middle", fontWeight = 700,
        color = "#FFFFFF", subtitleColor = "#E0E0E0",
        offset = 10, subtitlePadding = 4
    )
)

viz3 = alt.hconcat(v3_left_chart, v3_right_chart).resolve_scale(color = "independent")
save_chart(viz3, "pisa_gender_efficacy_dumbbell.json")
