import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart, COUNTRY_NAME_MAP, CONTINENT_MAP, INTERNET_USAGE_MAP, INTERNET_USAGE_ORDER

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory = False)

v3_data = pisa_df[(pisa_df["PV1MATH"].notna()) &
                   (pisa_df["PV1READ"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2])) &
                   (pisa_df["ST016Q01NA"].notna()) &
                   (pisa_df["CNT"].notna())].copy()

v3_data["Gender"] = v3_data["ST004D01T"].map({1: "Female", 2: "Male"})
v3_data["Country"] = v3_data["CNT"].map(COUNTRY_NAME_MAP).fillna(v3_data["CNT"])
v3_data["Continent"] = v3_data["CNT"].map(CONTINENT_MAP).fillna("Other")
v3_data["Internet_Usage"] = v3_data["ST016Q01NA"].astype(int).map(INTERNET_USAGE_MAP)
INTERNET_USAGE_GROUPED = {
    "None": "None/Low (0-2h)", "1-2h": "None/Low (0-2h)",
    "2-4h": "Moderate (2-6h)", "4-6h": "Moderate (2-6h)",
    "6-8h": "High (6-10h)", "8-10h": "High (6-10h)",
    "10-12h": "Extreme (10+h)", "12-14h": "Extreme (10+h)", "14-16h": "Extreme (10+h)", "16+h": "Extreme (10+h)", "Extreme": "Extreme (10+h)"
}
v3_data["Internet_Usage_Group"] = v3_data["Internet_Usage"].map(INTERNET_USAGE_GROUPED)

v3_internet_agg = v3_data.groupby("Internet_Usage_Group").agg(
    Math_Score = ("PV1MATH", "mean"),
    Reading_Score = ("PV1READ", "mean"),
    Count = ("PV1MATH", "count")
).reset_index()

v3_continent_gender = v3_data.groupby(["Continent", "Gender", "Internet_Usage_Group"]).agg(
    Math_Score = ("PV1MATH", "mean"),
    Reading_Score = ("PV1READ", "mean"),
    Count = ("PV1MATH", "count")
).reset_index()

v3_math_pivot = v3_continent_gender.pivot(index = ["Continent", "Internet_Usage_Group"], columns = "Gender", values = "Math_Score").reset_index()
v3_math_pivot.columns = ["Continent", "Internet_Usage_Group", "Female_Math", "Male_Math"]
v3_math_pivot["Math_Gap"] = v3_math_pivot["Male_Math"] - v3_math_pivot["Female_Math"]

v3_read_pivot = v3_continent_gender.pivot(index = ["Continent", "Internet_Usage_Group"], columns = "Gender", values = "Reading_Score").reset_index()
v3_read_pivot.columns = ["Continent", "Internet_Usage_Group", "Female_Read", "Male_Read"]
v3_read_pivot["Reading_Gap"] = v3_read_pivot["Male_Read"] - v3_read_pivot["Female_Read"]

v3_count_pivot = v3_continent_gender.pivot(index = ["Continent", "Internet_Usage_Group"], columns = "Gender", values = "Count").reset_index()
v3_count_pivot.columns = ["Continent", "Internet_Usage_Group", "Female_N", "Male_N"]

v3_gap_df = v3_math_pivot.merge(v3_read_pivot, on = ["Continent", "Internet_Usage_Group"]).merge(v3_count_pivot, on = ["Continent", "Internet_Usage_Group"])
v3_gap_df["Total_N"] = v3_gap_df["Female_N"] + v3_gap_df["Male_N"]
v3_gap_df = v3_gap_df.dropna()

v3_continent_order = ["Europe", "Asia", "North America", "South America", "Oceania", "Africa", "Other"]
v3_continent_colors = ["#4CAF50", "#FF9800", "#2196F3", "#9C27B0", "#00BCD4", "#FF5722", "#607D8B"]

v3_internet_colors = ["#1b5e20", "#2e7d32", "#388e3c", "#43a047", "#4caf50", "#66bb6a", "#81c784", "#a5d6a7", "#c8e6c9", "#e8f5e9", "#f1f8e9"]

v3_gap_long = v3_gap_df[["Continent", "Internet_Usage_Group", "Math_Gap", "Reading_Gap", "Total_N"]].melt(
    id_vars = ["Continent", "Internet_Usage_Group", "Total_N"],
    var_name = "Subject",
    value_name = "Gender_Gap"
)
v3_gap_long["Subject"] = v3_gap_long["Subject"].map({"Math_Gap": "Math", "Reading_Gap": "Reading"})

v3_internet_select = alt.selection_point(fields = ["Internet_Usage_Group"], name = "internet_select", empty = "all")

v3_group_order = ["None/Low (0-2h)", "Moderate (2-6h)", "High (6-10h)", "Extreme (10+h)"]
v3_group_colors = ["#2e7d32", "#4caf50", "#81c784", "#c8e6c9"]

v3_left_chart = alt.Chart(v3_internet_agg).mark_bar(
    stroke = "#0f172a", strokeWidth = 1, cursor = "pointer"
).encode(
    x = alt.X("Internet_Usage_Group:N", title = "Daily Internet Usage",
             sort = v3_group_order,
             axis = alt.Axis(labelFontSize = 10, titleFontSize = 12, labelAngle = -45)),
    y = alt.Y("Math_Score:Q", title = "Mean Math Score",
             scale = alt.Scale(domain = [390, 450], clamp = True),
             axis = alt.Axis(labelFontSize = 11, titleFontSize = 12, grid = True, gridOpacity = 0.3)),
    color = alt.condition(
        v3_internet_select,
        alt.Color("Internet_Usage_Group:N", title = "Usage",
                 scale = alt.Scale(domain = v3_group_order, range = v3_group_colors),
                 legend = None),
        alt.value("#444444")
    ),
    tooltip = [
        alt.Tooltip("Internet_Usage_Group:N", title = "Internet Usage"),
        alt.Tooltip("Math_Score:Q", title = "Mean Math Score", format = ".1f"),
        alt.Tooltip("Reading_Score:Q", title = "Mean Reading Score", format = ".1f"),
        alt.Tooltip("Count:Q", title = "Sample Size", format = ",d")
    ]
).add_params(v3_internet_select).properties(
    width = 350, height = 420,
    title = alt.TitleParams(
        text = "Mathematics Performance by Daily Internet Usage",
        subtitle = "Mean scores across usage intensity levels (PISA 2022)",
        fontSize = 15, subtitleFontSize = 11,
        font = "Roboto, sans-serif", anchor = "middle", fontWeight = 700,
        color = "#FFFFFF", subtitleColor = "#E0E0E0",
        offset = 10, subtitlePadding = 4
    )
)

v3_right_base = alt.Chart(v3_gap_long).transform_filter(
    v3_internet_select
)

v3_right_bars = v3_right_base.mark_bar(strokeWidth = 0.5).encode(
    x = alt.X("Continent:N", title = "Continent",
             sort = v3_continent_order,
             axis = alt.Axis(labelFontSize = 10, titleFontSize = 12, labelAngle = -30)),
    y = alt.Y("Gender_Gap:Q", title = "Gender Gap (Male - Female)",
             axis = alt.Axis(labelFontSize = 11, titleFontSize = 12, grid = True, gridOpacity = 0.3)),
    xOffset = "Subject:N",
    color = alt.Color("Subject:N", title = "Subject",
                     scale = alt.Scale(domain = ["Math", "Reading"], range = ["#E8A0BF", "#4169E1"]),
                     legend = alt.Legend(orient = "top", titleFontSize = 11, labelFontSize = 10,
                                        direction = "horizontal", symbolSize = 80)),
    tooltip = [
        alt.Tooltip("Continent:N", title = "Continent"),
        alt.Tooltip("Subject:N", title = "Subject"),
        alt.Tooltip("Gender_Gap:Q", title = "Gender Gap (M-F)", format = ".1f"),
        alt.Tooltip("Total_N:Q", title = "Sample Size", format = ",d")
    ]
).properties(
    width = 500, height = 420,
    title = alt.TitleParams(
        text = "Gender Disparities in Mathematics and Reading Achievement",
        subtitle = "Score differentials by geographic region (positive = male advantage)",
        fontSize = 15, subtitleFontSize = 11,
        font = "Roboto, sans-serif", anchor = "middle", fontWeight = 700,
        color = "#FFFFFF", subtitleColor = "#E0E0E0",
        offset = 10, subtitlePadding = 4
    )
)

v3_zero_line = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
    color = "#FFFFFF", strokeWidth = 1.5, strokeDash = [4, 4]
).encode(y = "y:Q")

v3_right_chart = alt.layer(v3_right_bars, v3_zero_line)

viz3 = alt.hconcat(v3_left_chart, v3_right_chart).resolve_scale(color = "independent").configure_view(
    stroke = None,
    fill = None
).properties(
    background = "transparent"
)
save_chart(viz3, "pisa_gender_efficacy_dumbbell.json")
