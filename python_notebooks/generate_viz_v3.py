import pandas as pd
import altair as alt
from pathlib import Path
import json
import numpy as np

alt.data_transformers.disable_max_rows()

DATA_DIR = Path("../data")
OUTPUT_DIR = Path("../assets/json")
OUTPUT_DIR.mkdir(parents = True, exist_ok = True)

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory = False)
hsls_df = pd.read_csv(DATA_DIR / "hsls_subset.csv", low_memory = False)

DARK_CONFIG = {
    "background": "#030712",
    "view": {"stroke": "transparent"},
    "axis": {
        "labelColor": "#E0E0E0",
        "titleColor": "#FFFFFF",
        "gridColor": "#333333",
        "domainColor": "#444444",
        "tickColor": "#444444"
    },
    "legend": {"labelColor": "#E0E0E0", "titleColor": "#FFFFFF"},
    "title": {"color": "#FFFFFF"}
}

GENDER_COLORS = {"Female": "#E91E63", "Male": "#1976D2"}


def save_chart(chart, filename):
    spec = json.loads(chart.to_json())
    spec["config"] = DARK_CONFIG
    with open(OUTPUT_DIR / filename, "w") as f:
        json.dump(spec, f, indent = 2)


pisa_v1 = pisa_df[(pisa_df["MATHEFF"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2]))].copy()
pisa_v1["Gender"] = pisa_v1["ST004D01T"].map({1: "Female", 2: "Male"})

country_names_v1 = {
    "USA": "United States", "GBR": "United Kingdom", "DEU": "Germany",
    "FRA": "France", "JPN": "Japan", "KOR": "South Korea", "AUS": "Australia",
    "CAN": "Canada", "NLD": "Netherlands", "SWE": "Sweden", "NOR": "Norway",
    "FIN": "Finland", "DNK": "Denmark", "CHE": "Switzerland", "AUT": "Austria",
    "BEL": "Belgium", "IRL": "Ireland", "NZL": "New Zealand", "SGP": "Singapore",
    "HKG": "Hong Kong", "TWN": "Taiwan", "ISR": "Israel", "ESP": "Spain",
    "ITA": "Italy", "PRT": "Portugal", "POL": "Poland", "CZE": "Czech Republic"
}
pisa_v1["Country"] = pisa_v1["CNT"].map(country_names_v1).fillna(pisa_v1["CNT"])

efficacy_by_gender = pisa_v1.groupby(["Country", "Gender"]).agg(
    Efficacy = ("MATHEFF", "mean"),
    Math_Score = ("PV1MATH", "mean"),
    Count = ("MATHEFF", "count")
).reset_index()

efficacy_pivot = efficacy_by_gender.pivot(index = "Country", columns = "Gender", values = "Efficacy").reset_index()
efficacy_pivot.columns = ["Country", "Female_Eff", "Male_Eff"]
efficacy_pivot["Efficacy_Gap"] = efficacy_pivot["Male_Eff"] - efficacy_pivot["Female_Eff"]
efficacy_pivot = efficacy_pivot.dropna()

score_pivot = efficacy_by_gender.pivot(index = "Country", columns = "Gender", values = "Math_Score").reset_index()
score_pivot.columns = ["Country", "Female_Score", "Male_Score"]
score_pivot["Score_Gap"] = score_pivot["Male_Score"] - score_pivot["Female_Score"]

count_pivot = efficacy_by_gender.pivot(index = "Country", columns = "Gender", values = "Count").reset_index()
count_pivot.columns = ["Country", "Female_N", "Male_N"]

gap_df = (
    efficacy_pivot
    .merge(score_pivot, on = "Country", how = "inner")
    .merge(count_pivot, on = "Country", how = "inner")
)
gap_df["Total_N"] = gap_df["Female_N"] + gap_df["Male_N"]
gap_df["Gap_Direction"] = np.where(gap_df["Efficacy_Gap"] >= 0, "Male higher efficacy", "Female higher efficacy")
gap_df["Abs_Efficacy_Gap"] = gap_df["Efficacy_Gap"].abs()
gap_df = gap_df.dropna()

top_gap_country = gap_df.loc[gap_df["Abs_Efficacy_Gap"].idxmax(), "Country"]

country_dropdown = alt.binding_select(
    options = sorted(gap_df["Country"].unique()),
    name = "Country: "
)
country_select = alt.selection_point(
    fields = ["Country"],
    bind = country_dropdown,
    value = [{"Country": top_gap_country}],
    name = "country_select"
)

zero_rule_x = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(
    color = "#374151", strokeDash = [4, 4], strokeWidth = 1
).encode(x = "x:Q")

zero_rule_y = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
    color = "#374151", strokeDash = [4, 4], strokeWidth = 1
).encode(y = "y:Q")

trend_line = alt.Chart(gap_df).transform_regression(
    "Efficacy_Gap", "Score_Gap", method = "linear"
).mark_line(stroke = "#9ca3af", strokeDash = [6, 4])

gap_scatter = alt.Chart(gap_df).mark_circle(
    size = 120, stroke = "#0b132b", strokeWidth = 0.6, cursor = "pointer"
).encode(
    x = alt.X("Efficacy_Gap:Q", title = "Male - Female self-efficacy",
             scale = alt.Scale(zero = True)),
    y = alt.Y("Score_Gap:Q", title = "Male - Female math score",
             scale = alt.Scale(zero = True)),
    color = alt.Color(
        "Efficacy_Gap:Q",
        title = "Efficacy gap (M-F)",
        scale = alt.Scale(scheme = "redblue", domainMid = 0)
    ),
    size = alt.Size("Total_N:Q", title = "Sample size",
                   scale = alt.Scale(range = [60, 520]), legend = None),
    opacity = alt.condition(country_select, alt.value(1.0), alt.value(0.45)),
    tooltip = [
        alt.Tooltip("Country:N", title = "Country"),
        alt.Tooltip("Efficacy_Gap:Q", title = "Efficacy gap (M-F)", format = ".2f"),
        alt.Tooltip("Score_Gap:Q", title = "Achievement gap (M-F)", format = ".1f"),
        alt.Tooltip("Female_Eff:Q", title = "Female efficacy", format = ".2f"),
        alt.Tooltip("Male_Eff:Q", title = "Male efficacy", format = ".2f"),
        alt.Tooltip("Female_Score:Q", title = "Female score", format = ".0f"),
        alt.Tooltip("Male_Score:Q", title = "Male score", format = ".0f"),
        alt.Tooltip("Total_N:Q", title = "Students", format = ",d")
    ]
).add_params(country_select)

selected_labels = alt.Chart(gap_df).transform_filter(country_select).mark_text(
    align = "left", dx = 6, dy = -6, fontSize = 11, fontWeight = "bold", color = "#e5e7eb"
).encode(
    x = "Efficacy_Gap:Q",
    y = "Score_Gap:Q",
    text = "Country:N"
)

left_chart_v1 = (zero_rule_x + zero_rule_y + trend_line + gap_scatter + selected_labels).properties(
    width = 620, height = 420,
    title = {
        "text": "Do confidence gaps translate to achievement gaps?",
        "subtitle": "Quadrants: right = male higher efficacy, left = female higher | Click/choose a country to inspect details",
        "color": "#FFFFFF", "fontSize": 15, "subtitleColor": "#E0E0E0", "subtitleFontSize": 11
    }
)

eff_long = gap_df[["Country", "Female_Eff", "Male_Eff"]].melt(id_vars = "Country", var_name = "Gender", value_name = "Value")
eff_long["Gender"] = eff_long["Gender"].str.replace("_Eff", "", regex = False)
eff_long["Metric"] = "Self-efficacy"

score_long = gap_df[["Country", "Female_Score", "Male_Score"]].melt(id_vars = "Country", var_name = "Gender", value_name = "Value")
score_long["Gender"] = score_long["Gender"].str.replace("_Score", "", regex = False)
score_long["Metric"] = "Math achievement"

detail_long = pd.concat([eff_long, score_long], ignore_index = True)
metric_order = ["Self-efficacy", "Math achievement"]

bar_base = alt.Chart(detail_long).transform_filter(country_select)

bars = bar_base.mark_bar(
    size = 22, cornerRadiusEnd = 3
).encode(
    x = alt.X("Value:Q", title = "Mean (selected country)"),
    y = alt.Y("Gender:N", title = "", sort = ["Female", "Male"]),
    color = alt.Color("Gender:N",
                     scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#3b82f6"]),
                     legend = None),
    tooltip = [
        alt.Tooltip("Metric:N", title = "Metric"),
        alt.Tooltip("Gender:N", title = "Gender"),
        alt.Tooltip("Value:Q", title = "Mean", format = ".2f")
    ]
).properties(width = 300, height = 120)

bar_labels = bar_base.mark_text(
    align = "left", dx = 6, dy = 0, fontSize = 11, color = "#e5e7eb"
).encode(
    x = alt.X("Value:Q"),
    y = alt.Y("Gender:N", sort = ["Female", "Male"]),
    text = alt.Text("Value:Q", format = ".2f")
)

right_chart_v1 = alt.layer(bars, bar_labels).facet(
    row = alt.Row("Metric:N", sort = metric_order, title = None, header = alt.Header(labelFontSize = 12))
).resolve_scale(x = "independent").properties(
    title = {
        "text": "Gender breakdown for selected country",
        "subtitle": "Bars show mean self-efficacy and math score",
        "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0", "subtitleFontSize": 11
    }
)

viz1 = alt.hconcat(left_chart_v1, right_chart_v1).resolve_scale(color = "independent")
save_chart(viz1, "pisa_gender_efficacy_dumbbell.json")


parent_edu_map_v2 = {
    1: "Less than HS", 1.0: "Less than HS",
    2: "HS Diploma/GED", 2.0: "HS Diploma/GED",
    3: "Associate's", 3.0: "Associate's",
    4: "Bachelor's", 4.0: "Bachelor's",
    5: "Master's", 5.0: "Master's",
    7: "Ph.D/Prof. Degree", 7.0: "Ph.D/Prof. Degree"
}
student_expect_map_v2 = {
    1: "HS or Less", 1.0: "HS or Less",
    2: "HS or Less", 2.0: "HS or Less",
    3: "Associate's", 3.0: "Associate's",
    4: "Associate's", 4.0: "Associate's",
    5: "Bachelor's", 5.0: "Bachelor's",
    6: "Bachelor's", 6.0: "Bachelor's",
    7: "Graduate/Prof", 7.0: "Graduate/Prof",
    8: "Graduate/Prof", 8.0: "Graduate/Prof",
    9: "Graduate/Prof", 9.0: "Graduate/Prof",
    10: "Graduate/Prof", 10.0: "Graduate/Prof",
    11: "Unknown", 11.0: "Unknown"
}
income_map_v2 = {
    1: 7500, 1.0: 7500, 2: 25000, 2.0: 25000, 3: 45000, 3.0: 45000,
    4: 65000, 4.0: 65000, 5: 85000, 5.0: 85000, 6: 105000, 6.0: 105000,
    7: 125000, 7.0: 125000, 8: 145000, 8.0: 145000, 9: 165000, 9.0: 165000,
    10: 185000, 10.0: 185000, 11: 205000, 11.0: 205000, 12: 225000, 12.0: 225000,
    13: 250000, 13.0: 250000
}
locale_map_v2 = {1: "City", 1.0: "City", 2: "Suburb", 2.0: "Suburb", 3: "Town", 3.0: "Town", 4: "Rural", 4.0: "Rural"}
stem_map_v2 = {0: 0, 0.0: 0, 1: 1, 1.0: 1, 2: 1, 2.0: 1, 3: 1, 3.0: 1, 4: 1, 4.0: 1, 5: 1, 5.0: 1, 6: 1, 6.0: 1}

hsls_v2 = hsls_df[(hsls_df["X1PAR1EDU"].notna()) &
                   (hsls_df["X1FAMINCOME"].notna()) &
                   (hsls_df["X1STUEDEXPCT"].notna()) &
                   (hsls_df["X1SEX"].isin([1, 2])) &
                   (hsls_df["X1LOCALE"].notna()) &
                   (hsls_df["X1STU30OCC_STEM1"].notna())].copy()

hsls_v2["parent_education"] = hsls_v2["X1PAR1EDU"].map(parent_edu_map_v2).fillna("Unknown")
hsls_v2["student_ed_expect"] = hsls_v2["X1STUEDEXPCT"].map(student_expect_map_v2).fillna("Unknown")
hsls_v2["family_income_numeric"] = hsls_v2["X1FAMINCOME"].map(income_map_v2)
hsls_v2["gender"] = hsls_v2["X1SEX"].map({1: "Male", 1.0: "Male", 2: "Female", 2.0: "Female"})
hsls_v2["school_locale"] = hsls_v2["X1LOCALE"].map(locale_map_v2).fillna("Unknown")
hsls_v2["expected_stem_2009"] = hsls_v2["X1STU30OCC_STEM1"].map(stem_map_v2)

parent_edu_order_v2 = ["Less than HS", "HS Diploma/GED", "Associate's", "Bachelor's", "Master's", "Ph.D/Prof. Degree"]
expect_order_v2 = ["HS or Less", "Associate's", "Bachelor's", "Graduate/Prof"]
locale_order_v2 = ["City", "Suburb", "Town", "Rural"]

income_df_v2 = hsls_v2[
    (hsls_v2["parent_education"].isin(parent_edu_order_v2)) &
    (hsls_v2["student_ed_expect"].isin(expect_order_v2)) &
    (hsls_v2["family_income_numeric"].notna())
].groupby(["parent_education", "student_ed_expect"]).agg(
    avg_income = ("family_income_numeric", "mean"),
    student_count = ("family_income_numeric", "count")
).reset_index()

stem_df_v2 = hsls_v2[
    (hsls_v2["school_locale"].isin(locale_order_v2)) &
    (hsls_v2["gender"].isin(["Male", "Female"])) &
    (hsls_v2["expected_stem_2009"].notna())
].groupby(["school_locale", "gender", "parent_education"]).agg(
    stem_rate = ("expected_stem_2009", "mean"),
    student_count = ("expected_stem_2009", "count")
).reset_index()

expect_colors_v2 = ["#E57373", "#FFB74D", "#81C784", "#64B5F6"]
gender_colors_v2 = ["#1976D2", "#E91E63"]

edu_selection_v2 = alt.selection_point(fields = ["parent_education"], name = "edu_select")

left_chart_v2 = alt.Chart(income_df_v2).mark_bar(
    cursor = "pointer", cornerRadiusTopRight = 3, cornerRadiusTopLeft = 3,
    stroke = "#0f172a", strokeWidth = 0.8
).encode(
    x = alt.X("parent_education:N", title = "Parent Education Level", sort = parent_edu_order_v2,
             axis = alt.Axis(labelAngle = -45, labelFontSize = 10, labelPadding = 8, titleFontSize = 14)),
    xOffset = alt.XOffset("student_ed_expect:N", sort = expect_order_v2),
    y = alt.Y("avg_income:Q", title = "Average Family Income ($)",
             axis = alt.Axis(labelFontSize = 12, titleFontSize = 14, grid = True, gridOpacity = 0.3, format = "$,.0f"),
             scale = alt.Scale(domain = [0, 180000])),
    color = alt.Color("student_ed_expect:N", title = "Student Expectations", sort = expect_order_v2,
                     scale = alt.Scale(domain = expect_order_v2, range = expect_colors_v2),
                     legend = alt.Legend(titleFontSize = 11, labelFontSize = 9, orient = "bottom",
                                        direction = "horizontal", symbolSize = 60, padding = 8,
                                        titlePadding = 8, columns = 4, offset = 10, labelLimit = 120)),
    opacity = alt.condition(edu_selection_v2, alt.value(1), alt.value(0.3)),
    tooltip = [alt.Tooltip("parent_education:N", title = "Parent Education"),
              alt.Tooltip("student_ed_expect:N", title = "Student Expectations"),
              alt.Tooltip("avg_income:Q", title = "Avg Family Income", format = "$,.0f"),
              alt.Tooltip("student_count:Q", title = "Students", format = ",d")]
).add_params(edu_selection_v2).properties(
    width = 450, height = 450,
    title = alt.TitleParams(
        text = "Family Income by Parent Education & Student Expectations",
        subtitle = "Click on a parent education level to filter the right chart",
        fontSize = 16,
        subtitleFontSize = 11,
        font = "Roboto, sans-serif",
        anchor = "middle",
        fontWeight = 700,
        color = "#FFFFFF",
        subtitleColor = "#E0E0E0",
        offset = 10,
        subtitlePadding = 4
    )
)

right_chart_v2 = alt.Chart(stem_df_v2).transform_filter(edu_selection_v2).mark_bar(
    cornerRadiusTopRight = 4, cornerRadiusBottomRight = 4,
    stroke = "#0f172a", strokeWidth = 0.8
).encode(
    y = alt.Y("school_locale:N", title = "School Location", sort = locale_order_v2,
             axis = alt.Axis(labelFontSize = 13, labelPadding = 8, titleFontSize = 14)),
    yOffset = alt.YOffset("gender:N", sort = ["Male", "Female"]),
    x = alt.X("mean(stem_rate):Q", title = "% Expecting STEM Career at Age 30",
             axis = alt.Axis(format = ".0%", labelFontSize = 12, titleFontSize = 14, grid = True, gridOpacity = 0.3, labelAngle = -45),
             scale = alt.Scale(domain = [0, 0.55])),
    color = alt.Color("gender:N", title = "Gender", sort = ["Male", "Female"],
                     scale = alt.Scale(domain = ["Male", "Female"], range = gender_colors_v2),
                     legend = alt.Legend(titleFontSize = 11, labelFontSize = 9, orient = "bottom",
                                        direction = "horizontal", symbolSize = 80, padding = 8,
                                        titlePadding = 8, columns = 2, offset = 10, labelLimit = 180)),
    tooltip = [alt.Tooltip("school_locale:N", title = "School Location"),
              alt.Tooltip("gender:N", title = "Gender"),
              alt.Tooltip("mean(stem_rate):Q", title = "STEM Rate", format = ".1%"),
              alt.Tooltip("sum(student_count):Q", title = "Students", format = ",d")]
).properties(
    width = 480, height = 450,
    title = alt.TitleParams(
        text = "STEM Career Expectations by School Location & Gender",
        subtitle = "Filtered by parent education selection from left chart",
        fontSize = 16,
        subtitleFontSize = 11,
        font = "Roboto, sans-serif",
        anchor = "middle",
        fontWeight = 700,
        color = "#FFFFFF",
        subtitleColor = "#E0E0E0",
        offset = 10,
        subtitlePadding = 4
    )
)

viz2 = alt.hconcat(left_chart_v2, right_chart_v2).resolve_scale(color = "independent")
save_chart(viz2, "hsls_math_identity_race.json")


race_map_v6 = {
    1: "Am. Indian/Alaska Native", 1.0: "Am. Indian/Alaska Native",
    2: "Asian", 2.0: "Asian",
    3: "Black/African American", 3.0: "Black/African American",
    4: "Hispanic", 4.0: "Hispanic",
    5: "Hispanic", 5.0: "Hispanic",
    6: "More than one race", 6.0: "More than one race",
    7: "Native Hawaiian/Pacific Islander", 7.0: "Native Hawaiian/Pacific Islander",
    8: "White", 8.0: "White"
}

region_state_map_v6 = {
    "Northeast": [9, 23, 25, 33, 44, 50, 34, 36, 42],
    "Midwest": [17, 18, 26, 39, 55, 19, 20, 27, 29, 31, 38, 46],
    "South": [10, 11, 12, 13, 24, 37, 45, 51, 54, 1, 21, 28, 40, 47, 48, 5, 22],
    "West": [4, 8, 16, 30, 32, 35, 49, 56, 2, 6, 15, 41, 53]
}

state_to_region_v6 = {}
for region, state_ids in region_state_map_v6.items():
    for state_id in state_ids:
        state_to_region_v6[state_id] = region

RACE_ORDER_V6 = ["White", "Black/African American", "Hispanic", "Asian", "More than one race", "Am. Indian/Alaska Native", "Native Hawaiian/Pacific Islander"]
RACE_COLORS_V6 = ["#0072B2", "#D55E00", "#E69F00", "#009E73", "#CC79A7", "#F0E442", "#56B4E9"]

hsls_v6 = hsls_df[(hsls_df["X1RACE"].notna()) &
                   (hsls_df["X3TGPA9TH"].notna()) &
                   (hsls_df["X4RFDGMJSTEM"].notna()) &
                   (hsls_df["X1REGION"].notna())].copy()
hsls_v6 = hsls_v6[(hsls_v6["X1RACE"] > 0) &
                   (hsls_v6["X1REGION"] > 0) &
                   (hsls_v6["X4RFDGMJSTEM"].isin([0, 1]))]

hsls_v6["race"] = hsls_v6["X1RACE"].map(race_map_v6).fillna("Unknown")
hsls_v6["is_stem_major"] = hsls_v6["X4RFDGMJSTEM"].map({0: 0, 1: 1})

region_mapping_v6 = {1: "Northeast", 2: "Midwest", 3: "South", 4: "West"}
hsls_v6["region"] = hsls_v6["X1REGION"].map(region_mapping_v6).fillna("Unknown")
hsls_v6 = hsls_v6[(hsls_v6["region"] != "Unknown") & (hsls_v6["race"] != "Unknown")]

gpa_cols_v6 = [("9th Grade", "X3TGPA9TH"), ("10th Grade", "X3TGPA10TH"),
               ("11th Grade", "X3TGPA11TH"), ("12th Grade", "X3TGPA12TH")]
gpa_frames_v6 = []
for label, col in gpa_cols_v6:
    series = pd.to_numeric(hsls_v6[col], errors = "coerce")
    frame = pd.DataFrame({
        "region": hsls_v6["region"],
        "race": hsls_v6["race"],
        "grade": label,
        "gpa": series
    })
    gpa_frames_v6.append(frame)
gpa_long_v6 = pd.concat(gpa_frames_v6, ignore_index = True)
gpa_long_v6 = gpa_long_v6.dropna(subset = ["gpa"])
gpa_long_v6 = gpa_long_v6[gpa_long_v6["gpa"] > 0]

gpa_agg_v6 = gpa_long_v6.groupby(["region", "race", "grade"]).agg(
    avg_gpa = ("gpa", "mean"),
    count = ("gpa", "size")
).reset_index()

national_grade_avg_v6 = gpa_long_v6.groupby("grade").agg(avg_gpa = ("gpa", "mean")).reset_index()

stem_rate_v6 = hsls_v6.groupby(["region", "race"]).agg(
    stem_share = ("is_stem_major", "mean"),
    n = ("is_stem_major", "size")
).reset_index()

region_summary_v6 = hsls_v6.groupby("region").agg(
    stem_count = ("is_stem_major", "sum"),
    total_students = ("is_stem_major", "size"),
    stem_share = ("is_stem_major", "mean")
).reset_index()

state_region_rows_v6 = []
for state_id, region in state_to_region_v6.items():
    state_region_rows_v6.append({"id": f"{state_id:02d}", "region": region})
state_region_df_v6 = pd.DataFrame(state_region_rows_v6)

merged_data_v6 = state_region_df_v6.merge(region_summary_v6, on = "region", how = "left")
merged_data_v6[["stem_count", "stem_share", "total_students"]] = merged_data_v6[["stem_count", "stem_share", "total_students"]].fillna(0)

region_label_positions = pd.DataFrame({
    "region": ["Northeast", "Midwest", "South", "West"],
    "lon": [-71, -93, -84, -117],
    "lat": [43.8, 44.5, 32.5, 38.5]
})
region_labels_v6 = region_label_positions.merge(region_summary_v6, on = "region", how = "left")
region_labels_v6["stem_label"] = region_labels_v6["stem_share"].apply(lambda x: f"{x * 100:.1f}% STEM")

us_topojson_url_v6 = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"
states_v6 = alt.topo_feature(us_topojson_url_v6, "states")

region_select_v6 = alt.selection_point(fields = ["region"], empty = True, name = "region_select")

geo_map_v6 = alt.Chart(states_v6).mark_geoshape(stroke = "white", strokeWidth = 2).encode(
    color = alt.condition(
        region_select_v6,
        alt.Color("stem_count:Q", title = "STEM Major Student Count",
                 scale = alt.Scale(scheme = "oranges", domain = [400, 1100]),
                 legend = alt.Legend(
                     format = ",d",
                     titleFontSize = 13,
                     labelFontSize = 11,
                     orient = "bottom",
                     direction = "horizontal",
                     gradientLength = 200,
                     gradientThickness = 12,
                     titlePadding = 10,
                     labelPadding = 8,
                     padding = 12,
                     offset = 15,
                     values = [400, 600, 800, 1000],
                     titleAnchor = "middle",
                     legendX = 138,
                     legendY = 410
                 )),
        alt.value("#F0F0F0")
    ),
    strokeWidth = alt.condition(region_select_v6, alt.value(3), alt.value(1.5)),
    tooltip = [
        alt.Tooltip("region:N", title = "Region"),
        alt.Tooltip("stem_count:Q", title = "STEM Major Students", format = ",d")
    ]
).transform_lookup(
    lookup = "id",
    from_ = alt.LookupData(merged_data_v6, "id", ["region", "stem_share", "stem_count", "total_students"])
).add_params(region_select_v6).project(type = "albersUsa").properties(
    width = 475, height = 400,
    title = alt.TitleParams(
        text = "Regional STEM Major Enrollment Counts in 2016",
        subtitle = "Click regions on the map to filter GPA trajectories by geographic area",
        fontSize = 20,
        subtitleFontSize = 14,
        font = "Roboto, sans-serif",
        anchor = "middle",
        fontWeight = 800,
        color = "#FFFFFF",
        subtitleColor = "#E0E0E0",
        offset = 10,
        subtitlePadding = 4
    )
)

gpa_line_v6 = alt.Chart(gpa_long_v6).transform_filter(region_select_v6).mark_line(
    point = alt.OverlayMarkDef(filled = True, size = 60),
    strokeWidth = 2.5
).encode(
    x = alt.X("grade:O", title = "Grade Level",
             sort = ["9th Grade", "10th Grade", "11th Grade", "12th Grade"],
             axis = alt.Axis(labelFontSize = 12, labelPadding = 10, titleFontSize = 14,
                           titleColor = "#FFFFFF", labelColor = "#E0E0E0", labelAngle = -45)),
    y = alt.Y("mean(gpa):Q", title = "Average GPA", scale = alt.Scale(domain = [1.9, 3.5]),
             axis = alt.Axis(format = ".2f", labelFontSize = 14, titleFontSize = 14,
                           titleColor = "#FFFFFF", labelColor = "#E0E0E0")),
    color = alt.Color("race:N", title = "Race/Ethnicity", sort = RACE_ORDER_V6,
                     scale = alt.Scale(domain = RACE_ORDER_V6, range = RACE_COLORS_V6),
                     legend = alt.Legend(titleFontSize = 11, labelFontSize = 10, orient = "bottom",
                                        direction = "horizontal", columns = 4, symbolSize = 80,
                                        padding = 8, offset = 10, titlePadding = 8, labelLimit = 150)),
    tooltip = [
        alt.Tooltip("race:N", title = "Race/Ethnicity"),
        alt.Tooltip("grade:O", title = "Grade"),
        alt.Tooltip("mean(gpa):Q", title = "Average GPA", format = ".2f"),
        alt.Tooltip("count():Q", title = "Students", format = ",d")
    ]
).properties(
    width = 475, height = 400,
    title = alt.TitleParams(
        text = "GPA Trajectories by Race/Ethnicity (9th-12th Grade)",
        subtitle = "Average GPA progression filtered by selected region",
        fontSize = 18,
        subtitleFontSize = 13,
        font = "Roboto, sans-serif",
        anchor = "middle",
        fontWeight = 800,
        color = "#FFFFFF",
        subtitleColor = "#E0E0E0",
        offset = 10,
        subtitlePadding = 4
    )
)

viz6 = alt.hconcat(geo_map_v6, gpa_line_v6).resolve_scale(color = "independent")
save_chart(viz6, "hsls_gpa_ses_trajectory.json")


pisa_v4 = pisa_df[(pisa_df["CNT"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["PV1READ"].notna()) &
                   (pisa_df["PV1SCIE"].notna())].copy()

country_names_v4 = {
    "USA": "United States", "GBR": "United Kingdom", "DEU": "Germany",
    "FRA": "France", "JPN": "Japan", "KOR": "South Korea", "AUS": "Australia",
    "CAN": "Canada", "NLD": "Netherlands", "SWE": "Sweden", "NOR": "Norway",
    "FIN": "Finland", "DNK": "Denmark", "CHE": "Switzerland", "AUT": "Austria",
    "BEL": "Belgium", "IRL": "Ireland", "NZL": "New Zealand", "SGP": "Singapore",
    "HKG": "Hong Kong", "MAC": "Macao", "TWN": "Taiwan", "ISR": "Israel",
    "POL": "Poland", "CZE": "Czech Republic", "SVN": "Slovenia", "EST": "Estonia",
    "LVA": "Latvia", "LTU": "Lithuania", "HUN": "Hungary", "SVK": "Slovakia",
    "PRT": "Portugal", "ESP": "Spain", "ITA": "Italy", "GRC": "Greece",
    "TUR": "Turkey", "CHL": "Chile", "MEX": "Mexico", "BRA": "Brazil",
    "ARG": "Argentina", "COL": "Colombia", "PER": "Peru", "URY": "Uruguay"
}

pisa_v4["Country"] = pisa_v4["CNT"].map(country_names_v4).fillna(pisa_v4["CNT"])

math_scores = pisa_v4.groupby("Country")["PV1MATH"].mean().reset_index()
math_scores.columns = ["Country", "Mean"]
math_scores["Domain"] = "MATH"
math_scores["Rank"] = math_scores["Mean"].rank(ascending = False)

read_scores = pisa_v4.groupby("Country")["PV1READ"].mean().reset_index()
read_scores.columns = ["Country", "Mean"]
read_scores["Domain"] = "READ"
read_scores["Rank"] = read_scores["Mean"].rank(ascending = False)

scie_scores = pisa_v4.groupby("Country")["PV1SCIE"].mean().reset_index()
scie_scores.columns = ["Country", "Mean"]
scie_scores["Domain"] = "SCIE"
scie_scores["Rank"] = scie_scores["Mean"].rank(ascending = False)

rankings_df = pd.concat([math_scores, read_scores, scie_scores], ignore_index = True)

top_countries_list = []
for domain in ["MATH", "READ", "SCIE"]:
    domain_top = rankings_df[rankings_df["Domain"] == domain].nsmallest(30, "Rank").copy()
    top_countries_list.append(domain_top)

rankings_top30 = pd.concat(top_countries_list, ignore_index = True)

click_domain = alt.selection_point(fields = ["Domain"], empty = True)

rankings_interactive = alt.Chart(rankings_top30).mark_circle(size = 60).encode(
    x = alt.X("Country:N",
             sort = alt.EncodingSortField(field = "Mean", order = "descending"),
             title = "Country",
             axis = alt.Axis(labelAngle = -45, labelFontSize = 10, titleFontSize = 12)),
    y = alt.Y("Mean:Q",
             title = "Score",
             scale = alt.Scale(domain = [460, 580])),
    color = alt.Color("Domain:N",
                     title = "Domain",
                     scale = alt.Scale(domain = ["MATH", "READ", "SCIE"],
                                      range = ["#1f77b4", "#2ca02c", "#d62728"]),
                     legend = alt.Legend(titleFontSize = 13, labelFontSize = 12)),
    opacity = alt.condition(click_domain, alt.value(1.0), alt.value(0.2)),
    tooltip = [alt.Tooltip("Country:N", title = "Country"),
              alt.Tooltip("Domain:N", title = "Domain"),
              alt.Tooltip("Mean:Q", title = "Score", format = ".1f"),
              alt.Tooltip("Rank:Q", title = "Rank", format = ".0f")]
).add_params(click_domain).properties(
    width = 550,
    height = 400,
    title = {"text": "Global Comparison of PISA Scores: Top 30 Countries by Domain",
            "subtitle": "Click data point to filter",
            "fontSize": 14,
            "fontWeight": "bold",
            "color": "#FFFFFF",
            "subtitleColor": "#E0E0E0"}
)

domain_avg = rankings_df.groupby("Domain").agg(
    Avg_Score = ("Mean", "mean"),
    N_Countries = ("Country", "count")
).reset_index()

bar_domain_avg = alt.Chart(domain_avg).mark_bar(cornerRadius = 4).encode(
    y = alt.Y("Domain:N", title = "Domain"),
    x = alt.X("Avg_Score:Q", title = "Global Average Score"),
    color = alt.Color("Domain:N",
                     scale = alt.Scale(domain = ["MATH", "READ", "SCIE"],
                                      range = ["#1f77b4", "#2ca02c", "#d62728"]),
                     legend = None),
    opacity = alt.condition(click_domain, alt.value(1.0), alt.value(0.3)),
    tooltip = [alt.Tooltip("Domain:N", title = "Domain"),
              alt.Tooltip("Avg_Score:Q", title = "Global Average", format = ".1f"),
              alt.Tooltip("N_Countries:Q", title = "Countries")]
).properties(
    width = 250,
    height = 400,
    title = {"text": "Global Averages",
            "fontSize": 14,
            "fontWeight": "bold",
            "color": "#FFFFFF"}
)

viz4 = alt.hconcat(rankings_interactive, bar_domain_avg).resolve_scale(color = "independent")
save_chart(viz4, "combined_gender_stem.json")


pisa_v5 = pisa_df[(pisa_df["ANXMAT"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2]))].copy()
pisa_v5["Gender"] = pisa_v5["ST004D01T"].map({1: "Female", 2: "Male"})

anxiety_terciles_v5 = pisa_v5["ANXMAT"].quantile([0, 0.33, 0.67, 1]).values
pisa_v5["Anxiety_Level"] = pd.cut(pisa_v5["ANXMAT"], bins = anxiety_terciles_v5,
                                   labels = ["Low", "Medium", "High"], include_lowest = True)

anxiety_counts_v5 = pisa_v5.groupby("Anxiety_Level").size().reset_index(name = "Count")

pisa_v5_sample = pisa_v5.sample(n = min(10000, len(pisa_v5)), random_state = 42)

anxiety_order_v5 = ["Low", "Medium", "High"]
anxiety_colors_v5 = ["#66BB6A", "#FFA726", "#EF5350"]

click_anxiety_v5 = alt.selection_point(fields = ["Anxiety_Level"], empty = True, name = "anxiety_select")

left_chart_v5 = alt.Chart(anxiety_counts_v5).mark_bar(cornerRadius = 4, cursor = "pointer").encode(
    x = alt.X("Anxiety_Level:N", title = "Math Anxiety Level", sort = anxiety_order_v5,
             axis = alt.Axis(labelAngle = 0, labelFontSize = 12)),
    y = alt.Y("Count:Q", title = "Number of Students"),
    color = alt.Color("Anxiety_Level:N", title = "Anxiety Level",
                     scale = alt.Scale(domain = anxiety_order_v5, range = anxiety_colors_v5),
                     legend = alt.Legend(orient = "top")),
    opacity = alt.condition(click_anxiety_v5, alt.value(1.0), alt.value(0.5)),
    tooltip = [alt.Tooltip("Anxiety_Level:N", title = "Anxiety Level"),
              alt.Tooltip("Count:Q", title = "Students", format = ",d")]
).add_params(click_anxiety_v5).properties(
    name = "view_1",
    title = {"text": "Students by Math Anxiety Level",
            "subtitle": "Click an anxiety level to see score distribution",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 420, height = 380
)

right_chart_v5 = alt.Chart(pisa_v5_sample).mark_boxplot(extent = "min-max", size = 40).encode(
    x = alt.X("Gender:N", title = "Gender",
             axis = alt.Axis(labelAngle = 0, labelFontSize = 12)),
    y = alt.Y("PV1MATH:Q", title = "Math Score (PV1MATH)",
             scale = alt.Scale(domain = [200, 700])),
    color = alt.Color("Gender:N",
                     scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]),
                     legend = alt.Legend(title = "Gender", orient = "top"))
).transform_filter(click_anxiety_v5).properties(
    title = {"text": "Math Score Distribution by Gender",
            "subtitle": "Filtered by anxiety level selection",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 450, height = 380
)

viz5 = alt.hconcat(left_chart_v5, right_chart_v5).resolve_scale(color = "independent")
save_chart(viz5, "pisa_anxiety_performance_heatmap.json")


immig_map_v6 = {1: "Native", 2: "Second-gen", 3: "First-gen"}
immig_order_v6 = ["Native", "Second-gen", "First-gen"]

pisa_v6 = pisa_df[(pisa_df["IMMIG"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2])) &
                   (pisa_df["BELONG"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["PV1READ"].notna()) &
                   (pisa_df["PV1SCIE"].notna())].copy()
pisa_v6 = pisa_v6[(pisa_v6["IMMIG"] > 0) & (pisa_v6["IMMIG"] <= 3)]

pisa_v6["Immigration_Status"] = pisa_v6["IMMIG"].map(immig_map_v6)
pisa_v6["Gender"] = pisa_v6["ST004D01T"].map({1: "Female", 2: "Male"})

immig_gender_belong_v6 = pisa_v6.groupby(["Immigration_Status", "Gender"]).agg(
    Avg_Belonging = ("BELONG", "mean"),
    Count = ("BELONG", "count")
).reset_index()

immig_select_v6 = alt.selection_point(fields = ["Immigration_Status"], name = "immig_select")

left_chart_v6 = alt.Chart(immig_gender_belong_v6).mark_bar(
    cornerRadius = 4, cursor = "pointer"
).encode(
    x = alt.X("Immigration_Status:N", title = "Immigration Status", sort = immig_order_v6,
             axis = alt.Axis(labelAngle = 0, labelFontSize = 11)),
    y = alt.Y("Avg_Belonging:Q", title = "Average School Belonging Score"),
    xOffset = alt.XOffset("Gender:N", sort = ["Female", "Male"]),
    color = alt.Color("Gender:N", title = "Gender",
                     scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]),
                     legend = alt.Legend(orient = "top")),
    opacity = alt.condition(immig_select_v6, alt.value(1), alt.value(0.4)),
    tooltip = ["Immigration_Status:N", "Gender:N",
              alt.Tooltip("Avg_Belonging:Q", format = ".2f", title = "Avg Belonging"),
              alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).add_params(immig_select_v6).properties(
    name = "view_1",
    title = {"text": "School Belonging by Immigration Status",
            "subtitle": "Click to see performance by domain",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 380, height = 400
)

immig_performance_v6 = pisa_v6.groupby("Immigration_Status").agg(
    Math = ("PV1MATH", "mean"),
    Reading = ("PV1READ", "mean"),
    Science = ("PV1SCIE", "mean"),
    Count = ("PV1MATH", "count")
).reset_index()

immig_perf_long_v6 = immig_performance_v6.melt(
    id_vars = ["Immigration_Status", "Count"],
    value_vars = ["Math", "Reading", "Science"],
    var_name = "Domain",
    value_name = "Avg_Score"
)

right_chart_v6 = alt.Chart(immig_perf_long_v6).mark_bar(cornerRadius = 4).encode(
    x = alt.X("Domain:N", title = None, sort = ["Math", "Reading", "Science"],
             axis = alt.Axis(labelAngle = 0, labelFontSize = 11)),
    y = alt.Y("Avg_Score:Q", title = "Average Score", scale = alt.Scale(domain = [400, 520])),
    xOffset = alt.XOffset("Immigration_Status:N", sort = immig_order_v6),
    color = alt.Color("Immigration_Status:N", title = "Immigration Status",
                     scale = alt.Scale(domain = immig_order_v6,
                                      range = ["#4CAF50", "#FF9800", "#9C27B0"]),
                     legend = alt.Legend(orient = "top")),
    opacity = alt.condition(immig_select_v6, alt.value(1), alt.value(0.3)),
    tooltip = [alt.Tooltip("Immigration_Status:N", title = "Status"),
              alt.Tooltip("Domain:N", title = "Domain"),
              alt.Tooltip("Avg_Score:Q", format = ".1f", title = "Avg Score")]
).properties(
    title = {"text": "Performance by Domain & Immigration Status",
            "subtitle": "Filtered by immigration status selection",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 400, height = 400
)

viz6 = alt.hconcat(left_chart_v6, right_chart_v6).resolve_scale(color = "independent")
save_chart(viz6, "combined_immigration.json")


pisa_v7 = pisa_df[(pisa_df["ESCS"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["CNT"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2]))].copy()

pv_cols = [f"PV{i}MATH" for i in range(1, 11)]
available_pv = [col for col in pv_cols if col in pisa_v7.columns]
pisa_v7["Math_Score"] = pisa_v7[available_pv].mean(axis = 1)
pisa_v7["Gender"] = pisa_v7["ST004D01T"].map({1: "Female", 2: "Male"})

country_gender_agg = pisa_v7.groupby(["CNT", "Gender"]).agg(
    Mean_ESCS = ("ESCS", "mean"),
    Mean_Math = ("Math_Score", "mean"),
    n = ("CNT", "size")
).reset_index()

OECD_V7 = {
    "AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "COL", "CRI", "CZE", "DEU",
    "DNK", "ESP", "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISL",
    "ITA", "JPN", "KOR", "LTU", "LVA", "MEX", "NLD", "NOR", "NZL", "POL",
    "PRT", "SVK", "SVN", "SWE", "TUR", "USA"
}
country_gender_agg["OECD_Status"] = country_gender_agg["CNT"].apply(
    lambda x: "OECD" if x in OECD_V7 else "Non-OECD"
)
country_gender_agg["Gender_OECD"] = country_gender_agg["Gender"] + " " + country_gender_agg["OECD_Status"]

hsls_v7 = hsls_df[(hsls_df["X1TXMQUINT"].notna()) &
                   (hsls_df["X1STUEDEXPCT"].notna()) &
                   (hsls_df["X1SESQ5"].notna()) &
                   (hsls_df["X1SEX"].isin([1, 2]))].copy()
hsls_v7 = hsls_v7[(hsls_v7["X1TXMQUINT"] > 0) &
                   (hsls_v7["X1STUEDEXPCT"] > 0) &
                   (hsls_v7["X1SESQ5"] > 0)]

hsls_v7["Gender"] = hsls_v7["X1SEX"].map({1: "Male", 2: "Female"})
hsls_v7["Math_Quintile"] = hsls_v7["X1TXMQUINT"].map({
    1: "Q1 (Lowest)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (Highest)"
})
hsls_v7["SES_Quintile"] = hsls_v7["X1SESQ5"].map({
    1: "Q1 (Lowest)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (Highest)"
})
hsls_v7["Ed_Expect_Num"] = hsls_v7["X1STUEDEXPCT"]

hsls_agg = hsls_v7.groupby(["Gender", "Math_Quintile", "SES_Quintile"]).agg(
    Mean_Ed_Expect = ("Ed_Expect_Num", "mean"),
    n = ("Ed_Expect_Num", "size")
).reset_index()

brush_select = alt.selection_interval(name = "brush_select")

quintile_order = ["Q1 (Lowest)", "Q2", "Q3", "Q4", "Q5 (Highest)"]
ses_colors = ["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"]

gender_oecd_domain = ["Female OECD", "Female Non-OECD", "Male OECD", "Male Non-OECD"]
gender_oecd_colors = ["#E91E63", "#F48FB1", "#1976D2", "#64B5F6"]

left_chart = alt.Chart(country_gender_agg).mark_circle(size = 80, cursor = "crosshair").encode(
    x = alt.X("Mean_ESCS:Q", title = "Mean SES (ESCS)",
              scale = alt.Scale(domain = [-2.5, 1.0])),
    y = alt.Y("Mean_Math:Q", title = "Mean Math Score (PV1-10)",
              scale = alt.Scale(domain = [300, 600])),
    color = alt.Color("Gender_OECD:N",
                   scale = alt.Scale(domain = gender_oecd_domain, range = gender_oecd_colors),
                   legend = alt.Legend(title = "Gender & OECD", orient = "top")),
    opacity = alt.condition(brush_select, alt.value(1), alt.value(0.3)),
    tooltip = [
        alt.Tooltip("CNT:N", title = "Country"),
        alt.Tooltip("Gender:N"),
        alt.Tooltip("OECD_Status:N", title = "OECD Status"),
        alt.Tooltip("Mean_ESCS:Q", title = "Mean SES", format = ".2f"),
        alt.Tooltip("Mean_Math:Q", title = "Mean Math", format = ".0f"),
        alt.Tooltip("n:Q", title = "Students", format = ",d")
    ]
).add_params(brush_select).properties(
    name = "view_1",
    title = {"text": "PISA: Country-Level SES vs Math",
           "subtitle": "Drag to select and highlight countries",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 320, height = 300
)

right_chart = alt.Chart(hsls_agg).mark_bar(clip = True).encode(
    x = alt.X("Math_Quintile:N", title = "Math Quintile", sort = quintile_order,
            axis = alt.Axis(labelAngle = -45),
            scale = alt.Scale(paddingOuter = 0.2)),
    y = alt.Y("Mean_Ed_Expect:Q", title = "Mean Ed Expectation Level",
            scale = alt.Scale(domain = [5.5, 9.0], zero = False)),
    color = alt.Color("SES_Quintile:N", title = "SES Quintile",
                   scale = alt.Scale(domain = quintile_order, range = ses_colors),
                   legend = alt.Legend(orient = "top")),
    xOffset = alt.XOffset("SES_Quintile:N", sort = quintile_order,
                         scale = alt.Scale(paddingInner = 0.2)),
    tooltip = [
        alt.Tooltip("Math_Quintile:N", title = "Math Quintile"),
        alt.Tooltip("SES_Quintile:N", title = "SES Quintile"),
        alt.Tooltip("Mean_Ed_Expect:Q", title = "Mean Ed Expectation", format = ".2f"),
        alt.Tooltip("n:Q", title = "Students", format = ",d")
    ]
).properties(
    title = {"text": "HSLS: Math Level vs Ed Expectations",
           "subtitle": "Education expectations by math and SES quintile",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 450, height = 300
)

viz7 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz7, "combined_efficacy_comparison.json")


continent_map = {
    "USA": "North America", "CAN": "North America", "MEX": "North America", "PAN": "North America",
    "CRI": "North America", "DOM": "North America", "JAM": "North America", "PRI": "North America",
    "BRA": "South America", "ARG": "South America", "CHL": "South America", "COL": "South America",
    "PER": "South America", "URY": "South America", "ECU": "South America",
    "GBR": "Europe", "FRA": "Europe", "DEU": "Europe", "ESP": "Europe", "ITA": "Europe",
    "PRT": "Europe", "NLD": "Europe", "BEL": "Europe", "LUX": "Europe", "CHE": "Europe",
    "AUT": "Europe", "SWE": "Europe", "NOR": "Europe", "DNK": "Europe", "FIN": "Europe",
    "ISL": "Europe", "IRL": "Europe", "POL": "Europe", "CZE": "Europe", "SVK": "Europe",
    "HUN": "Europe", "SVN": "Europe", "EST": "Europe", "LVA": "Europe", "LTU": "Europe",
    "GRC": "Europe", "TUR": "Europe", "ROU": "Europe", "BGR": "Europe", "HRV": "Europe",
    "SRB": "Europe", "MNE": "Europe", "ALB": "Europe", "BIH": "Europe", "MKD": "Europe",
    "CHN": "Asia", "HKG": "Asia", "MAC": "Asia", "TWN": "Asia", "JPN": "Asia", "KOR": "Asia",
    "SGP": "Asia", "THA": "Asia", "VNM": "Asia", "IDN": "Asia", "MYS": "Asia", "PHL": "Asia",
    "KAZ": "Asia", "QAT": "Asia", "ARE": "Asia", "SAU": "Asia", "JOR": "Asia", "LBN": "Asia",
    "KWT": "Asia", "OMN": "Asia", "BHR": "Asia", "IND": "Asia", "PAK": "Asia", "BGD": "Asia",
    "LAO": "Asia", "KHM": "Asia",
    "ZAF": "Africa", "MAR": "Africa", "TUN": "Africa", "EGY": "Africa", "SEN": "Africa",
    "AUS": "Oceania", "NZL": "Oceania", "FJI": "Oceania",
}

pisa_v8 = pisa_df[["CNT", "ESCS", "MATHEFF", "MATHPERS", "ST004D01T"]].copy()
pisa_v8 = pisa_v8[(pisa_v8["ESCS"].notna()) &
                   (pisa_v8["MATHEFF"].notna()) &
                   (pisa_v8["MATHPERS"].notna()) &
                   (pisa_v8["ST004D01T"].isin([1, 2]))]
pisa_v8 = pisa_v8.assign(source = "PISA")
pisa_v8["continent"] = pisa_v8["CNT"].map(continent_map).fillna("Other")

hsls_v8 = hsls_df[["X1SES", "X1MTHEFF", "X1STU30OCC_STEM1", "X1SEX"]].copy()
hsls_v8 = hsls_v8[(hsls_v8["X1SES"] > -1) &
                   (hsls_v8["X1MTHEFF"] > -1) &
                   (hsls_v8["X1STU30OCC_STEM1"] >= 0) &
                   (hsls_v8["X1SEX"].isin([1, 2]))]
hsls_v8 = hsls_v8.assign(CNT = "USA", continent = "North America", source = "HSLS")

pisa_base_v8 = pisa_v8.rename(columns = {"ESCS": "escs", "MATHEFF": "matheff"})[["continent", "escs", "matheff"]].copy()
pisa_base_v8 = pisa_base_v8.dropna(subset = ["escs", "matheff", "continent"])
pisa_base_v8["z_escs"] = (pisa_base_v8["escs"] - pisa_base_v8["escs"].mean()) / pisa_base_v8["escs"].std(ddof = 0)
pisa_base_v8["z_matheff"] = (pisa_base_v8["matheff"] - pisa_base_v8["matheff"].mean()) / pisa_base_v8["matheff"].std(ddof = 0)

continent_agg = (
    pisa_base_v8.groupby("continent")
    .agg(avg_escs = ("z_escs", "mean"), avg_matheff = ("z_matheff", "mean"), n = ("z_escs", "size"))
    .reset_index()
)

pisa_students = (
    pisa_v8.rename(columns = {"ST004D01T": "gender"})
    .assign(
        continent = lambda d: d["CNT"].map(continent_map).fillna("Other"),
        source = "PISA",
        gender = lambda d: d["gender"].map({1: "Female", 2: "Male"}),
        stem_interest = lambda d: d["MATHPERS"],
    )
    [["continent", "gender", "stem_interest", "source"]]
    .dropna(subset = ["stem_interest", "gender", "continent"])
)
hsls_students = (
    hsls_v8.rename(columns = {"X1SEX": "gender"})
    .assign(
        source = "HSLS",
        gender = lambda d: d["gender"].map({1: "Male", 2: "Female"}),
        stem_interest = lambda d: d["X1STU30OCC_STEM1"],
    )
    [["continent", "gender", "stem_interest", "source"]]
    .dropna(subset = ["stem_interest", "gender", "continent"])
)
hsls_students = hsls_students[hsls_students["stem_interest"].isin([0, 1, 2, 3, 4, 5, 6])]
students_v8 = pd.concat([pisa_students, hsls_students], ignore_index = True)

sampled_students = students_v8.groupby(["continent", "gender"]).apply(
    lambda x: x.sample(n = min(len(x), 2000), random_state = 42)
).reset_index(drop = True)

continent_select = alt.selection_point(
    fields = ["continent"],
    name = "continent_select",
    empty = True
)

left_chart = (
    alt.Chart(continent_agg)
    .mark_circle(cursor = "pointer")
    .encode(
        x = alt.X("avg_escs:Q", title = "Mean SES (z within source)"),
        y = alt.Y("avg_matheff:Q", title = "Mean Math Self-Efficacy (z within source)"),
        size = alt.Size("n:Q", scale = alt.Scale(range = [60, 500]), legend = None),
        color = alt.Color("continent:N", title = "Continent/Region"),
        opacity = alt.condition(continent_select, alt.value(1), alt.value(0.4)),
        tooltip = [
            alt.Tooltip("continent:N", title = "Continent"),
            alt.Tooltip("avg_escs:Q", title = "Mean SES", format = ".2f"),
            alt.Tooltip("avg_matheff:Q", title = "Mean Math Efficacy", format = ".2f"),
            alt.Tooltip("n:Q", title = "Sample Size", format = ",d")
        ],
    )
    .add_params(continent_select)
    .properties(
        name = "view_1",
        title = {"text": "Continent SES vs Math Self-Efficacy (Standardized)", "subtitle": "Click a continent to filter",
                "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
        width = 280, height = 240
    )
)

right_chart = (
    alt.Chart(sampled_students)
    .transform_filter(continent_select)
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
        title = {"text": "STEM Interest by Gender (Selected Continent)", "subtitle": "Click continent on left to filter",
                "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
        width = 280, height = 240
    )
)

viz8 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz8, "combined_ses_achievement.json")


OECD_V9 = {
    "AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "COL", "CRI", "CZE", "DEU",
    "DNK", "ESP", "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISL",
    "ITA", "JPN", "KOR", "LTU", "LVA", "MEX", "NLD", "NOR", "NZL", "POL",
    "PRT", "SVK", "SVN", "SWE", "TUR", "USA"
}

pisa_cols_v9 = ["CNT", "ST004D01T", "ANXMAT"]
pisa_v9 = pisa_df[pisa_cols_v9].copy()
pisa_v9 = pisa_v9[(pisa_v9["ST004D01T"].isin([1, 2])) & (pisa_v9["ANXMAT"].notna())]
pisa_v9["Gender"] = pisa_v9["ST004D01T"].map({1: "Female", 2: "Male"})

country_gender_agg = pisa_v9.groupby(["CNT", "Gender"]).agg(
    Mean_Anxiety = ("ANXMAT", "mean"),
    n = ("ANXMAT", "count")
).reset_index()

country_gender_agg["OECD_Status"] = country_gender_agg["CNT"].apply(
    lambda x: "OECD" if x in OECD_V9 else "Non-OECD"
)

country_means = country_gender_agg.groupby("CNT")["Mean_Anxiety"].mean().reset_index()
country_means = country_means.sort_values("Mean_Anxiety", ascending = False)
top_30_countries = country_means.head(30)["CNT"].tolist()

dumbbell_data = country_gender_agg[country_gender_agg["CNT"].isin(top_30_countries)]

lines_data = dumbbell_data.pivot(index = ["CNT", "OECD_Status"], columns = "Gender", values = "Mean_Anxiety").reset_index()
lines_data.columns.name = None
lines_data = lines_data.rename(columns = {"Female": "Female_Anxiety", "Male": "Male_Anxiety"})

lines = alt.Chart(lines_data).mark_rule(strokeWidth = 1.5, opacity = 0.6).encode(
    y = alt.Y("CNT:N", title = "Country", sort = alt.EncodingSortField(field = "Female_Anxiety", order = "descending")),
    x = alt.X("Female_Anxiety:Q", title = "Mathematics Anxiety", scale = alt.Scale(domain = [-0.6, 0.8])),
    x2 = alt.X2("Male_Anxiety:Q"),
    color = alt.Color("OECD_Status:N", scale = alt.Scale(domain = ["OECD", "Non-OECD"], range = ["#1976D2", "#E91E63"]), title = "OECD Status")
)

points = alt.Chart(dumbbell_data).mark_point(size = 100, filled = True).encode(
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

left_chart = (lines + points).properties(
    title = {"text": "PISA: Math Anxiety by Country and Gender", "subtitle": "Dumbbell chart showing gender gap within countries",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 500, height = 500
)

hsls_cols_v9 = ["X1SEX", "X1MTHEFF"]
hsls_v9 = hsls_df[hsls_cols_v9].copy()
hsls_v9 = hsls_v9[(hsls_v9["X1SEX"].isin([1, 2])) & (hsls_v9["X1MTHEFF"].notna())]
hsls_v9["Gender"] = hsls_v9["X1SEX"].map({1: "Male", 2: "Female"})

hsls_sampled = hsls_v9.groupby("Gender", group_keys = False).apply(
    lambda x: x.sample(min(len(x), 5000), random_state = 42)
).reset_index(drop = True)

right_chart = alt.Chart(hsls_sampled).transform_density(
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

viz9 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz9, "combined_parent_education.json")
