import pandas as pd
import altair as alt
from pathlib import Path
import json

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


country_names_v1 = {
    "SGP": "Singapore", "MAC": "Macao", "TWN": "Taiwan", "HKG": "Hong Kong",
    "JPN": "Japan", "KOR": "South Korea", "EST": "Estonia", "CHE": "Switzerland",
    "CAN": "Canada", "NLD": "Netherlands", "IRL": "Ireland", "BEL": "Belgium",
    "DNK": "Denmark", "GBR": "UK", "POL": "Poland", "AUT": "Austria",
    "AUS": "Australia", "CZE": "Czech Rep.", "SVN": "Slovenia", "FIN": "Finland",
    "DEU": "Germany", "FRA": "France", "USA": "USA", "NZL": "New Zealand",
    "SWE": "Sweden", "NOR": "Norway", "ISL": "Iceland", "LUX": "Luxembourg",
    "ESP": "Spain", "ITA": "Italy", "PRT": "Portugal", "GRC": "Greece",
    "TUR": "Turkey", "MEX": "Mexico", "CHL": "Chile", "ISR": "Israel",
    "HUN": "Hungary", "SVK": "Slovakia", "LTU": "Lithuania", "LVA": "Latvia"
}

pisa_v1 = pisa_df[(pisa_df["MATHEFF"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2]))].copy()
pisa_v1["Gender"] = pisa_v1["ST004D01T"].map({1: "Female", 2: "Male"})
pisa_v1["Country"] = pisa_v1["CNT"].map(country_names_v1).fillna(pisa_v1["CNT"])

efficacy_by_gender = pisa_v1.groupby(["Country", "Gender"]).agg(
    Efficacy = ("MATHEFF", "mean"),
    Math_Score = ("PV1MATH", "mean"),
    Count = ("MATHEFF", "count")
).reset_index()

efficacy_pivot = efficacy_by_gender.pivot(index = "Country", columns = "Gender", values = "Efficacy").reset_index()
efficacy_pivot["Efficacy_Gap"] = efficacy_pivot["Male"] - efficacy_pivot["Female"]
efficacy_pivot = efficacy_pivot.dropna(subset = ["Efficacy_Gap"])
efficacy_pivot = efficacy_pivot.nlargest(25, "Efficacy_Gap").copy()

math_pivot = efficacy_by_gender.pivot(index = "Country", columns = "Gender", values = "Math_Score").reset_index()
math_pivot["Achievement_Gap"] = math_pivot["Male"] - math_pivot["Female"]

gap_data = efficacy_pivot.merge(math_pivot[["Country", "Achievement_Gap"]], on = "Country", how = "left")
gap_data["Gap_Direction"] = gap_data["Efficacy_Gap"].apply(lambda x: "Male Higher" if x > 0 else "Female Higher")

country_select_v1 = alt.selection_point(fields = ["Country"], empty = True, name = "country_select")

left_chart = alt.Chart(gap_data).mark_bar(cornerRadius = 4, cursor = "pointer").encode(
    y = alt.Y("Country:N", title = "Country",
             sort = alt.EncodingSortField(field = "Efficacy_Gap", order = "descending"),
             axis = alt.Axis(labelFontSize = 10, labelLimit = 150)),
    x = alt.X("Efficacy_Gap:Q", title = "Gender Gap in Self-Efficacy (Male - Female)",
             axis = alt.Axis(format = ".2f")),
    color = alt.Color("Gap_Direction:N",
                     scale = alt.Scale(domain = ["Male Higher", "Female Higher"], range = ["#1976D2", "#E91E63"]),
                     legend = alt.Legend(title = "Gap Direction", orient = "top")),
    opacity = alt.condition(country_select_v1, alt.value(1.0), alt.value(0.5)),
    tooltip = [alt.Tooltip("Country:N"),
              alt.Tooltip("Efficacy_Gap:Q", title = "Efficacy Gap", format = ".3f"),
              alt.Tooltip("Achievement_Gap:Q", title = "Achievement Gap", format = ".1f")]
).add_params(country_select_v1).properties(
    name = "view_1",
    title = {"text": "Gender Gap in Math Self-Efficacy",
            "subtitle": "Click a country to see achievement gap",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 380, height = 400
)

dumbbell_data = efficacy_by_gender[efficacy_by_gender["Country"].isin(gap_data["Country"])].copy()
dumbbell_data = dumbbell_data.melt(id_vars = ["Country", "Gender", "Count"],
                                    value_vars = ["Efficacy", "Math_Score"],
                                    var_name = "Measure", value_name = "Score")
dumbbell_data["Measure"] = dumbbell_data["Measure"].map({"Efficacy": "Self-Efficacy", "Math_Score": "Math Achievement"})

points = alt.Chart(dumbbell_data).mark_circle(size = 100).encode(
    y = alt.Y("Measure:N", title = "Measure",
             axis = alt.Axis(labelFontSize = 12)),
    x = alt.X("Score:Q", title = "Score (Standardized for Efficacy, Raw for Math)",
             scale = alt.Scale(zero = False)),
    color = alt.Color("Gender:N",
                     scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]),
                     legend = alt.Legend(title = "Gender", orient = "top")),
    tooltip = [alt.Tooltip("Country:N"),
              alt.Tooltip("Gender:N"),
              alt.Tooltip("Measure:N"),
              alt.Tooltip("Score:Q", format = ".2f"),
              alt.Tooltip("Count:Q", title = "Students", format = ",d")]
).transform_filter(country_select_v1)

right_chart = points.properties(
    title = {"text": "Gender Comparison by Country",
            "subtitle": "Efficacy and Achievement by Gender",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 350, height = 400
)

viz1 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz1, "pisa_gender_efficacy_dumbbell.json")


pisa_v2 = pisa_df[(pisa_df["ANXMAT"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2]))].copy()
pisa_v2["Gender"] = pisa_v2["ST004D01T"].map({1: "Female", 2: "Male"})

anxiety_terciles = pisa_v2["ANXMAT"].quantile([0, 0.33, 0.67, 1]).values
pisa_v2["Anxiety_Level"] = pd.cut(pisa_v2["ANXMAT"], bins = anxiety_terciles,
                                   labels = ["Low", "Medium", "High"], include_lowest = True)

anxiety_counts = pisa_v2.groupby("Anxiety_Level").size().reset_index(name = "Count")

pisa_v2_sample = pisa_v2.sample(n = min(10000, len(pisa_v2)), random_state = 42)

anxiety_order = ["Low", "Medium", "High"]
anxiety_colors = ["#66BB6A", "#FFA726", "#EF5350"]

click_anxiety = alt.selection_point(fields = ["Anxiety_Level"], empty = True, name = "anxiety_select")

left_chart = alt.Chart(anxiety_counts).mark_bar(cornerRadius = 4, cursor = "pointer").encode(
    x = alt.X("Anxiety_Level:N", title = "Math Anxiety Level", sort = anxiety_order,
             axis = alt.Axis(labelAngle = 0, labelFontSize = 12)),
    y = alt.Y("Count:Q", title = "Number of Students"),
    color = alt.Color("Anxiety_Level:N", title = "Anxiety Level",
                     scale = alt.Scale(domain = anxiety_order, range = anxiety_colors),
                     legend = alt.Legend(orient = "top")),
    opacity = alt.condition(click_anxiety, alt.value(1.0), alt.value(0.5)),
    tooltip = [alt.Tooltip("Anxiety_Level:N", title = "Anxiety Level"),
              alt.Tooltip("Count:Q", title = "Students", format = ",d")]
).add_params(click_anxiety).properties(
    name = "view_1",
    title = {"text": "Students by Math Anxiety Level",
            "subtitle": "Click an anxiety level to see score distribution",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 300, height = 350
)

right_chart = alt.Chart(pisa_v2_sample).mark_boxplot(extent = "min-max", size = 40).encode(
    x = alt.X("Gender:N", title = "Gender",
             axis = alt.Axis(labelAngle = 0, labelFontSize = 12)),
    y = alt.Y("PV1MATH:Q", title = "Math Score (PV1MATH)",
             scale = alt.Scale(domain = [200, 700])),
    color = alt.Color("Gender:N",
                     scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]),
                     legend = alt.Legend(title = "Gender", orient = "top"))
).transform_filter(click_anxiety).properties(
    title = {"text": "Math Score Distribution by Gender",
            "subtitle": "Filtered by anxiety level selection",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 350, height = 350
)

viz2 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz2, "pisa_anxiety_performance_heatmap.json")


immig_map = {1: "Native", 2: "Second-gen", 3: "First-gen"}
immig_order = ["Native", "Second-gen", "First-gen"]

pisa_v3 = pisa_df[(pisa_df["IMMIG"].notna()) &
                   (pisa_df["LANGN"].notna()) &
                   (pisa_df["BELONG"].notna()) &
                   (pisa_df["PV1MATH"].notna())].copy()
pisa_v3 = pisa_v3[(pisa_v3["IMMIG"] > 0) & (pisa_v3["IMMIG"] <= 3)]

pisa_v3["Immigration_Status"] = pisa_v3["IMMIG"].map(immig_map)
pisa_v3["Language_Home"] = pisa_v3["LANGN"].apply(lambda x: "Test Language" if x == 1 else "Other Language")

immig_lang_belong = pisa_v3.groupby(["Immigration_Status", "Language_Home"]).agg(
    Avg_Belonging = ("BELONG", "mean"),
    Count = ("BELONG", "count")
).reset_index()

pisa_v3_sample = pisa_v3.sample(n = min(5000, len(pisa_v3)), random_state = 42)

immig_select = alt.selection_point(fields = ["Immigration_Status"], name = "immig_select")
lang_colors = ["#1976D2", "#E91E63"]

left_chart = alt.Chart(immig_lang_belong).mark_bar(
    cornerRadius = 4, cursor = "pointer"
).encode(
    x = alt.X("Immigration_Status:N", title = "Immigration Status", sort = immig_order,
             axis = alt.Axis(labelAngle = 0, labelFontSize = 11)),
    y = alt.Y("Avg_Belonging:Q", title = "Average School Belonging Score"),
    xOffset = alt.XOffset("Language_Home:N", sort = ["Test Language", "Other Language"]),
    color = alt.Color("Language_Home:N", title = "Language at Home",
                     scale = alt.Scale(domain = ["Test Language", "Other Language"], range = lang_colors),
                     legend = alt.Legend(orient = "top")),
    opacity = alt.condition(immig_select, alt.value(1), alt.value(0.4)),
    tooltip = ["Immigration_Status:N", "Language_Home:N",
              alt.Tooltip("Avg_Belonging:Q", format = ".2f", title = "Avg Belonging"),
              alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).add_params(immig_select).properties(
    name = "view_1",
    title = {"text": "School Belonging by Immigration Status",
            "subtitle": "Click to see belonging-achievement relationship",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 320, height = 350
)

right_chart = alt.Chart(pisa_v3_sample).mark_circle(size = 30, opacity = 0.5).encode(
    x = alt.X("BELONG:Q", title = "School Belonging Score",
             scale = alt.Scale(domain = [-3, 3])),
    y = alt.Y("PV1MATH:Q", title = "Math Score (PV1MATH)",
             scale = alt.Scale(domain = [200, 700])),
    color = alt.Color("Immigration_Status:N", title = "Immigration",
                     scale = alt.Scale(domain = immig_order,
                                      range = ["#4CAF50", "#FF9800", "#9C27B0"]),
                     legend = alt.Legend(orient = "top")),
    tooltip = [alt.Tooltip("Immigration_Status:N", title = "Status"),
              alt.Tooltip("BELONG:Q", format = ".2f", title = "Belonging"),
              alt.Tooltip("PV1MATH:Q", format = ".0f", title = "Math Score")]
).transform_filter(immig_select).properties(
    title = {"text": "Belonging vs Math Achievement",
            "subtitle": "Filtered by immigration status selection",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 350, height = 350
)

viz3 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz3, "combined_immigration.json")


ses_quintile_map_v4 = {1: "Q1 (Lowest)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (Highest)"}
ses_order_v4 = ["Q1 (Lowest)", "Q2", "Q3", "Q4", "Q5 (Highest)"]
race_map_v4 = {
    1: "Am. Indian/Alaska Native", 2: "Asian", 3: "Black/African American",
    4: "Hispanic", 5: "Hispanic", 6: "More than one race",
    7: "Native Hawaiian/Pac. Isl.", 8: "White"
}
race_order_v4 = ["White", "Asian", "Hispanic", "Black/African American", "More than one race",
                 "Am. Indian/Alaska Native", "Native Hawaiian/Pac. Isl."]

hsls_v4 = hsls_df[(hsls_df["S4RESEARCH"].notna()) &
                   (hsls_df["S4RESEARCH"] >= 0) &
                   (hsls_df["X1SESQ5"].notna()) &
                   (hsls_df["X1SESQ5"] > 0) &
                   (hsls_df["X1SEX"].isin([1, 2])) &
                   (hsls_df["X1RACE"].notna()) &
                   (hsls_df["X1RACE"] > 0)].copy()

hsls_v4["SES_Quintile"] = hsls_v4["X1SESQ5"].map(ses_quintile_map_v4)
hsls_v4["Gender"] = hsls_v4["X1SEX"].map({1: "Male", 2: "Female"})
hsls_v4["Race"] = hsls_v4["X1RACE"].map(race_map_v4).fillna("Unknown")
hsls_v4["Research_Exp"] = hsls_v4["S4RESEARCH"]

ses_research = hsls_v4.groupby("SES_Quintile").agg(
    Research_Rate = ("Research_Exp", "mean"),
    Count = ("Research_Exp", "count")
).reset_index()

research_by_race_gender = hsls_v4.groupby(["SES_Quintile", "Race", "Gender"]).agg(
    Research_Rate = ("Research_Exp", "mean"),
    Count = ("Research_Exp", "count")
).reset_index()
research_by_race_gender = research_by_race_gender[research_by_race_gender["Race"].isin(race_order_v4)]

ses_select_v4 = alt.selection_point(fields = ["SES_Quintile"], empty = True, name = "ses_select")

left_chart = alt.Chart(ses_research).mark_bar(cornerRadius = 4, cursor = "pointer").encode(
    x = alt.X("SES_Quintile:N", title = "SES Quintile", sort = ses_order_v4,
             axis = alt.Axis(labelAngle = -45, labelFontSize = 11)),
    y = alt.Y("Research_Rate:Q", title = "% with Research Experience",
             axis = alt.Axis(format = ".0%")),
    color = alt.value("#4CAF50"),
    opacity = alt.condition(ses_select_v4, alt.value(1.0), alt.value(0.5)),
    tooltip = [alt.Tooltip("SES_Quintile:N", title = "SES Quintile"),
              alt.Tooltip("Research_Rate:Q", title = "Research Rate", format = ".1%"),
              alt.Tooltip("Count:Q", title = "Students", format = ",d")]
).add_params(ses_select_v4).properties(
    name = "view_1",
    title = {"text": "Research Experience by SES Quintile",
            "subtitle": "Click to filter by socioeconomic status",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 380, height = 350
)

right_chart = alt.Chart(research_by_race_gender).mark_bar(cornerRadiusTopRight = 4, cornerRadiusBottomRight = 4).encode(
    y = alt.Y("Race:N", title = "Race/Ethnicity", sort = race_order_v4,
             axis = alt.Axis(labelFontSize = 11)),
    yOffset = alt.YOffset("Gender:N", sort = ["Male", "Female"]),
    x = alt.X("Research_Rate:Q", title = "% with Research Experience",
             axis = alt.Axis(format = ".0%"),
             scale = alt.Scale(domain = [0, 0.25])),
    color = alt.Color("Gender:N",
                     scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]),
                     legend = alt.Legend(title = "Gender", orient = "top")),
    tooltip = [alt.Tooltip("SES_Quintile:N", title = "SES Quintile"),
              alt.Tooltip("Race:N", title = "Race/Ethnicity"),
              alt.Tooltip("Gender:N"),
              alt.Tooltip("Research_Rate:Q", title = "Research Rate", format = ".1%"),
              alt.Tooltip("Count:Q", title = "Students", format = ",d")]
).transform_filter(ses_select_v4).properties(
    title = {"text": "Research Experience by Race & Gender",
            "subtitle": "Filtered by SES selection",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 380, height = 350
)

viz4 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz4, "combined_gender_stem.json")


parent_edu_map_v5 = {
    1: "Less than HS", 1.0: "Less than HS",
    2: "HS Diploma/GED", 2.0: "HS Diploma/GED",
    3: "Associate's", 3.0: "Associate's",
    4: "Bachelor's", 4.0: "Bachelor's",
    5: "Master's", 5.0: "Master's",
    7: "Ph.D/Prof. Degree", 7.0: "Ph.D/Prof. Degree"
}
student_expect_map = {
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
income_map_v5 = {
    1: 7500, 1.0: 7500, 2: 25000, 2.0: 25000, 3: 45000, 3.0: 45000,
    4: 65000, 4.0: 65000, 5: 85000, 5.0: 85000, 6: 105000, 6.0: 105000,
    7: 125000, 7.0: 125000, 8: 145000, 8.0: 145000, 9: 165000, 9.0: 165000,
    10: 185000, 10.0: 185000, 11: 205000, 11.0: 205000, 12: 225000, 12.0: 225000,
    13: 250000, 13.0: 250000
}
locale_map_v5 = {1: "City", 1.0: "City", 2: "Suburb", 2.0: "Suburb", 3: "Town", 3.0: "Town", 4: "Rural", 4.0: "Rural"}
stem_map_v5 = {0: 0, 0.0: 0, 1: 1, 1.0: 1, 2: 1, 2.0: 1, 3: 1, 3.0: 1, 4: 1, 4.0: 1, 5: 1, 5.0: 1, 6: 1, 6.0: 1}

hsls_v5 = hsls_df[(hsls_df["X1PAR1EDU"].notna()) &
                   (hsls_df["X1FAMINCOME"].notna()) &
                   (hsls_df["X1STUEDEXPCT"].notna()) &
                   (hsls_df["X1SEX"].isin([1, 2])) &
                   (hsls_df["X1LOCALE"].notna()) &
                   (hsls_df["X1STU30OCC_STEM1"].notna())].copy()

hsls_v5["parent_education"] = hsls_v5["X1PAR1EDU"].map(parent_edu_map_v5).fillna("Unknown")
hsls_v5["student_ed_expect"] = hsls_v5["X1STUEDEXPCT"].map(student_expect_map).fillna("Unknown")
hsls_v5["family_income_numeric"] = hsls_v5["X1FAMINCOME"].map(income_map_v5)
hsls_v5["gender"] = hsls_v5["X1SEX"].map({1: "Male", 1.0: "Male", 2: "Female", 2.0: "Female"})
hsls_v5["school_locale"] = hsls_v5["X1LOCALE"].map(locale_map_v5).fillna("Unknown")
hsls_v5["expected_stem_2009"] = hsls_v5["X1STU30OCC_STEM1"].map(stem_map_v5)

parent_edu_order_v5 = ["Less than HS", "HS Diploma/GED", "Associate's", "Bachelor's", "Master's", "Ph.D/Prof. Degree"]
expect_order = ["HS or Less", "Associate's", "Bachelor's", "Graduate/Prof"]
locale_order_v5 = ["City", "Suburb", "Town", "Rural"]

income_df = hsls_v5[
    (hsls_v5["parent_education"].isin(parent_edu_order_v5)) &
    (hsls_v5["student_ed_expect"].isin(expect_order)) &
    (hsls_v5["family_income_numeric"].notna())
].groupby(["parent_education", "student_ed_expect"]).agg(
    avg_income = ("family_income_numeric", "mean"),
    student_count = ("family_income_numeric", "count")
).reset_index()

stem_df = hsls_v5[
    (hsls_v5["school_locale"].isin(locale_order_v5)) &
    (hsls_v5["gender"].isin(["Male", "Female"])) &
    (hsls_v5["expected_stem_2009"].notna())
].groupby(["school_locale", "gender", "parent_education"]).agg(
    stem_rate = ("expected_stem_2009", "mean"),
    student_count = ("expected_stem_2009", "count")
).reset_index()

expect_colors = ["#E57373", "#FFB74D", "#81C784", "#64B5F6"]
gender_colors_v5 = ["#1976D2", "#E91E63"]

edu_selection = alt.selection_point(fields = ["parent_education"], name = "edu_select")

left_chart = alt.Chart(income_df).mark_bar(
    cursor = "pointer", cornerRadiusTopRight = 3, cornerRadiusTopLeft = 3
).encode(
    x = alt.X("parent_education:N", title = "Parent Education Level", sort = parent_edu_order_v5,
             axis = alt.Axis(labelAngle = -45, labelFontSize = 10, labelPadding = 8, titleFontSize = 14)),
    xOffset = alt.XOffset("student_ed_expect:N", sort = expect_order),
    y = alt.Y("avg_income:Q", title = "Average Family Income ($)",
             axis = alt.Axis(labelFontSize = 12, titleFontSize = 14, grid = True, gridOpacity = 0.3, format = "$,.0f"),
             scale = alt.Scale(domain = [0, 180000])),
    color = alt.Color("student_ed_expect:N", title = "Student Expectations", sort = expect_order,
                     scale = alt.Scale(domain = expect_order, range = expect_colors),
                     legend = alt.Legend(titleFontSize = 11, labelFontSize = 9, orient = "bottom",
                                        direction = "horizontal", symbolSize = 60, padding = 8,
                                        titlePadding = 8, columns = 4, offset = 10, labelLimit = 120)),
    opacity = alt.condition(edu_selection, alt.value(1), alt.value(0.3)),
    tooltip = [alt.Tooltip("parent_education:N", title = "Parent Education"),
              alt.Tooltip("student_ed_expect:N", title = "Student Expectations"),
              alt.Tooltip("avg_income:Q", title = "Avg Family Income", format = "$,.0f"),
              alt.Tooltip("student_count:Q", title = "Students", format = ",d")]
).add_params(edu_selection).properties(
    name = "view_1",
    title = {"text": "Family Income by Parent Education & Student Expectations",
            "subtitle": "Click on a parent education level to filter the right chart",
            "color": "#FFFFFF", "fontSize": 16, "subtitleColor": "#E0E0E0", "subtitleFontSize": 11},
    width = 450, height = 450
)

right_chart = alt.Chart(stem_df).transform_filter(edu_selection).mark_bar(
    cornerRadiusTopRight = 4, cornerRadiusBottomRight = 4
).encode(
    y = alt.Y("school_locale:N", title = "School Location", sort = locale_order_v5,
             axis = alt.Axis(labelFontSize = 13, labelPadding = 8, titleFontSize = 14)),
    yOffset = alt.YOffset("gender:N", sort = ["Male", "Female"]),
    x = alt.X("mean(stem_rate):Q", title = "% Expecting STEM Career at Age 30",
             axis = alt.Axis(format = ".0%", labelFontSize = 12, titleFontSize = 14, grid = True, gridOpacity = 0.3, labelAngle = -45),
             scale = alt.Scale(domain = [0, 0.55])),
    color = alt.Color("gender:N", title = "Gender", sort = ["Male", "Female"],
                     scale = alt.Scale(domain = ["Male", "Female"], range = gender_colors_v5),
                     legend = alt.Legend(titleFontSize = 11, labelFontSize = 9, orient = "bottom",
                                        direction = "horizontal", symbolSize = 80, padding = 8,
                                        titlePadding = 8, columns = 2, offset = 10, labelLimit = 180)),
    tooltip = [alt.Tooltip("school_locale:N", title = "School Location"),
              alt.Tooltip("gender:N", title = "Gender"),
              alt.Tooltip("mean(stem_rate):Q", title = "STEM Rate", format = ".1%"),
              alt.Tooltip("sum(student_count):Q", title = "Students", format = ",d")]
).properties(
    title = {"text": "STEM Career Expectations by School Location & Gender",
            "subtitle": "Filtered by parent education selection from left chart",
            "color": "#FFFFFF", "fontSize": 16, "subtitleColor": "#E0E0E0", "subtitleFontSize": 11},
    width = 480, height = 450
)

viz5 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz5, "hsls_math_identity_race.json")


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

region_state_map = {
    "Northeast": [9, 23, 25, 33, 44, 50, 34, 36, 42],
    "Midwest": [17, 18, 26, 39, 55, 19, 20, 27, 29, 31, 38, 46],
    "South": [10, 11, 12, 13, 24, 37, 45, 51, 54, 1, 21, 28, 40, 47, 48, 5, 22],
    "West": [4, 8, 16, 30, 32, 35, 49, 56, 2, 6, 15, 41, 53]
}

state_to_region = {}
for region, state_ids in region_state_map.items():
    for state_id in state_ids:
        state_to_region[state_id] = region

RACE_ORDER = ["White", "Black/African American", "Hispanic", "Asian", "More than one race", "Am. Indian/Alaska Native", "Native Hawaiian/Pacific Islander"]
RACE_COLORS = ["#0072B2", "#D55E00", "#E69F00", "#009E73", "#CC79A7", "#F0E442", "#56B4E9"]

hsls_v6 = hsls_df[(hsls_df["X1RACE"].notna()) &
                   (hsls_df["X3TGPA9TH"].notna()) &
                   (hsls_df["X4RFDGMJSTEM"].notna()) &
                   (hsls_df["X1REGION"].notna())].copy()
hsls_v6 = hsls_v6[(hsls_v6["X1RACE"] > 0) &
                   (hsls_v6["X1REGION"] > 0) &
                   (hsls_v6["X4RFDGMJSTEM"] >= 0)]

hsls_v6["race"] = hsls_v6["X1RACE"].map(race_map_v6).fillna("Unknown")
hsls_v6["is_stem_major"] = hsls_v6["X4RFDGMJSTEM"].map({0: 0, 0.0: 0, 1: 1, 1.0: 1})

region_mapping = {1: "Northeast", 2: "Midwest", 3: "South", 4: "West"}
hsls_v6["region"] = hsls_v6["X1REGION"].map(region_mapping).fillna("Unknown")

region_summary = hsls_v6[hsls_v6["is_stem_major"] == 1].groupby("region").agg(
    stem_count = ("is_stem_major", "sum")
).reset_index()
region_summary = region_summary[region_summary["region"] != "Unknown"]

state_region_rows = []
for state_id, region in state_to_region.items():
    state_region_rows.append({"id": f"{state_id:02d}", "region": region})
state_region_df = pd.DataFrame(state_region_rows)

merged_data = state_region_df.merge(region_summary, on = "region", how = "left")
merged_data["stem_count"] = merged_data["stem_count"].fillna(0)

us_topojson_url = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"
states = alt.topo_feature(us_topojson_url, "states")

click_region = alt.selection_point(fields = ["region"], empty = True, name = "region_select")

geo_map = alt.Chart(states).mark_geoshape(
    stroke = "white", strokeWidth = 2
).encode(
    color = alt.condition(
        click_region,
        alt.Color("stem_count:Q", title = "STEM Major Student Count",
                 scale = alt.Scale(scheme = "oranges", domain = [400, 1100]),
                 legend = alt.Legend(format = ",d", titleFontSize = 11, labelFontSize = 10,
                                    orient = "bottom", direction = "horizontal",
                                    gradientLength = 200, gradientThickness = 12,
                                    titlePadding = 10, labelPadding = 8, padding = 12, offset = 15)),
        alt.value("#F0F0F0")
    ),
    strokeWidth = alt.condition(click_region, alt.value(3), alt.value(1.5)),
    tooltip = [alt.Tooltip("region:N", title = "Region"),
              alt.Tooltip("stem_count:Q", title = "STEM Major Students", format = ",d")]
).transform_lookup(
    lookup = "id",
    from_ = alt.LookupData(merged_data, "id", ["region", "stem_count"])
).add_params(click_region).project(type = "albersUsa").properties(
    name = "view_1",
    title = {"text": "Regional STEM Major Enrollment Counts in 2016",
            "subtitle": "Click regions on the map to filter GPA trajectories by geographic area",
            "color": "#FFFFFF", "fontSize": 20, "subtitleColor": "#E0E0E0", "subtitleFontSize": 14},
    width = 475, height = 400
)

gpa_cols_v6 = [("9th Grade", "X3TGPA9TH"), ("10th Grade", "X3TGPA10TH"),
               ("11th Grade", "X3TGPA11TH"), ("12th Grade", "X3TGPA12TH")]
gpa_frames = []
for label, col in gpa_cols_v6:
    series = pd.to_numeric(hsls_v6[col], errors = "coerce")
    frame = pd.DataFrame({
        "region": hsls_v6["region"],
        "race": hsls_v6["race"],
        "grade": label,
        "gpa": series
    })
    gpa_frames.append(frame)
gpa_long = pd.concat(gpa_frames, ignore_index = True)
gpa_long = gpa_long.dropna(subset = ["gpa"])
gpa_long = gpa_long[gpa_long["gpa"] > 0]

gpa_line = alt.Chart(gpa_long).transform_filter(click_region).mark_line(
    point = alt.OverlayMarkDef(filled = True, size = 60), strokeWidth = 2.5
).encode(
    x = alt.X("grade:O", title = "Grade Level",
             sort = ["9th Grade", "10th Grade", "11th Grade", "12th Grade"],
             axis = alt.Axis(labelFontSize = 12, labelPadding = 10, titleFontSize = 14,
                           titleColor = "#FFFFFF", labelColor = "#E0E0E0", labelAngle = -45)),
    y = alt.Y("mean(gpa):Q", title = "Average GPA", scale = alt.Scale(domain = [2.0, 3.5]),
             axis = alt.Axis(format = ".2f", labelFontSize = 14, titleFontSize = 14,
                           titleColor = "#FFFFFF", labelColor = "#E0E0E0")),
    color = alt.Color("race:N", title = "Race/Ethnicity", sort = RACE_ORDER,
                     scale = alt.Scale(domain = RACE_ORDER, range = RACE_COLORS),
                     legend = alt.Legend(titleFontSize = 11, labelFontSize = 10, orient = "bottom",
                                        direction = "horizontal", columns = 4, symbolSize = 80,
                                        padding = 8, offset = 10, titlePadding = 8, labelLimit = 150)),
    tooltip = [alt.Tooltip("race:N", title = "Race/Ethnicity"),
              alt.Tooltip("grade:O", title = "Grade"),
              alt.Tooltip("mean(gpa):Q", title = "Average GPA", format = ".2f"),
              alt.Tooltip("count():Q", title = "Students", format = ",d")]
).properties(
    title = {"text": "GPA Trajectories by Race/Ethnicity (9th-12th Grade)",
            "subtitle": "Average GPA progression filtered by selected region",
            "color": "#FFFFFF", "fontSize": 18, "subtitleColor": "#E0E0E0", "subtitleFontSize": 13},
    width = 475, height = 400
)

viz6 = alt.hconcat(geo_map, gpa_line).resolve_scale(color = "independent")
save_chart(viz6, "hsls_gpa_ses_trajectory.json")


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
            scale = alt.Scale(domain = [5.5, 9.0])),
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

base_v8 = pd.concat([
    pisa_v8.rename(columns = {"ESCS": "escs", "MATHEFF": "matheff"})[["continent", "escs", "matheff", "source"]],
    hsls_v8.rename(columns = {"X1SES": "escs", "X1MTHEFF": "matheff"})[["continent", "escs", "matheff", "source"]],
], ignore_index = True)
base_v8 = base_v8.dropna(subset = ["escs", "matheff", "continent", "source"])
base_v8["z_escs"] = base_v8.groupby("source")["escs"].transform(lambda x: (x - x.mean()) / x.std(ddof = 0))
base_v8["z_matheff"] = base_v8.groupby("source")["matheff"].transform(lambda x: (x - x.mean()) / x.std(ddof = 0))

continent_agg = (
    base_v8.groupby("continent")
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


OECD_COUNTRIES = {
    "AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "COL", "CRI", "CZE", "DEU",
    "DNK", "ESP", "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISL",
    "ITA", "JPN", "KOR", "LTU", "LVA", "MEX", "NLD", "NOR", "NZL", "POL",
    "PRT", "SVK", "SVN", "SWE", "TUR", "USA"
}

OECD_SELECTED = ["USA", "GBR", "DEU", "FRA", "JPN", "AUS", "CAN", "NZL",
                 "FIN", "NOR", "SWE", "KOR", "EST", "POL", "MEX"]
NON_OECD_SELECTED = ["SGP", "HKG", "TAP", "MAC", "BRA", "ARG", "URY",
                     "ARE", "QAT", "SAU", "VNM", "MYS", "ROU", "SRB", "BGR"]
SELECTED_COUNTRIES = OECD_SELECTED + NON_OECD_SELECTED

pisa_v9 = pisa_df[
    (pisa_df["ANXMAT"].notna()) &
    (pisa_df["ST004D01T"].isin([1, 2])) &
    (pisa_df["CNT"].isin(SELECTED_COUNTRIES))
].copy()
pisa_v9["Gender"] = pisa_v9["ST004D01T"].map({1: "Female", 2: "Male"})
pisa_v9["OECD_Status"] = pisa_v9["CNT"].apply(
    lambda x: "OECD" if x in OECD_COUNTRIES else "Non-OECD"
)

anxiety_by_gender = pisa_v9.groupby(["CNT", "Gender", "OECD_Status"]).agg(
    Mean_Anxiety = ("ANXMAT", "mean")
).reset_index()

anxiety_wide = anxiety_by_gender.pivot(
    index = ["CNT", "OECD_Status"],
    columns = "Gender",
    values = "Mean_Anxiety"
).reset_index()
anxiety_wide.columns.name = None

gender_select = alt.selection_point(fields = ["Gender"], empty = True, name = "gender_select")

lines = alt.Chart(anxiety_wide).mark_rule(strokeWidth = 1.5).encode(
    y = alt.Y("CNT:N",
              title = "Country",
              sort = alt.EncodingSortField(field = "Female", order = "ascending"),
              axis = alt.Axis(labelFontSize = 10)),
    x = alt.X("Female:Q", title = "Mathematics Anxiety (Mean)"),
    x2 = alt.X2("Male:Q"),
    color = alt.Color("OECD_Status:N",
                      scale = alt.Scale(domain = ["OECD", "Non-OECD"],
                                       range = ["#1976D2", "#FF9800"]),
                      legend = None),
    opacity = alt.condition(gender_select, alt.value(0.6), alt.value(0.2))
)

points = alt.Chart(anxiety_by_gender).mark_point(size = 100, filled = True, cursor = "pointer").encode(
    y = alt.Y("CNT:N",
              sort = alt.EncodingSortField(field = "Mean_Anxiety", order = "ascending")),
    x = alt.X("Mean_Anxiety:Q"),
    color = alt.Color("OECD_Status:N",
                      scale = alt.Scale(domain = ["OECD", "Non-OECD"],
                                       range = ["#1976D2", "#FF9800"]),
                      legend = alt.Legend(title = "OECD Status", orient = "top")),
    shape = alt.Shape("Gender:N",
                      scale = alt.Scale(domain = ["Female", "Male"],
                                       range = ["square", "circle"]),
                      legend = alt.Legend(title = "Gender", orient = "top")),
    opacity = alt.condition(gender_select, alt.value(1.0), alt.value(0.4)),
    tooltip = [alt.Tooltip("CNT:N", title = "Country"),
               alt.Tooltip("Gender:N"),
               alt.Tooltip("OECD_Status:N", title = "OECD"),
               alt.Tooltip("Mean_Anxiety:Q", format = ".3f", title = "Anxiety")]
).add_params(gender_select)

left_chart = (lines + points).properties(
    name = "view_1",
    title = {
        "text": "Gender Gap in Math Anxiety by Country",
        "subtitle": "Click gender points to filter histogram | Square = Female, Circle = Male",
        "color": "#FFFFFF",
        "fontSize": 14,
        "subtitleColor": "#E0E0E0"
    },
    width = 400,
    height = 450
)

hsls_v9 = hsls_df[
    (hsls_df["X1MTHEFF"] >= -5) &
    (hsls_df["X1SEX"].isin([1, 2]))
][["X1MTHEFF", "X1SEX"]].copy()
hsls_v9["Gender"] = hsls_v9["X1SEX"].map({1: "Male", 2: "Female"})
hsls_v9 = hsls_v9[["X1MTHEFF", "Gender"]]

right_chart = alt.Chart(hsls_v9).transform_filter(
    gender_select
).transform_density(
    density = "X1MTHEFF",
    groupby = ["Gender"],
    as_ = ["X1MTHEFF", "density"]
).mark_area(opacity = 0.5).encode(
    x = alt.X("X1MTHEFF:Q",
              title = "Math Self-Efficacy",
              scale = alt.Scale(domain = [-3.5, 2.0])),
    y = alt.Y("density:Q", title = "Density"),
    color = alt.Color("Gender:N",
                      scale = alt.Scale(domain = ["Female", "Male"],
                                       range = ["#E91E63", "#1976D2"]),
                      legend = alt.Legend(title = "Gender", orient = "top"))
).properties(
    title = {
        "text": "Math Self-Efficacy Distribution by Gender (US)",
        "subtitle": "Filtered by gender selection from left chart",
        "color": "#FFFFFF",
        "fontSize": 14,
        "subtitleColor": "#E0E0E0"
    },
    width = 350,
    height = 450
)

viz9 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz9, "combined_parent_education.json")
