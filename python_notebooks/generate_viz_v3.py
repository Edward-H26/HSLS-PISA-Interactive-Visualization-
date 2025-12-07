import pandas as pd
import altair as alt
from pathlib import Path
import json
import numpy as np
from vega_datasets import data as vega_data

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

OKABE_ITO = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
GENDER_COLORS = {"Female": "#E91E63", "Male": "#1976D2"}

def save_chart(chart, filename):
    spec = json.loads(chart.to_json())
    spec["config"] = DARK_CONFIG
    with open(OUTPUT_DIR / filename, "w") as f:
        json.dump(spec, f, indent = 2)


# =============================================================================
# VIZ 1: Family Education Background & Math Achievement
# Left: Heatmap (Parent Education x Confidence -> Math Score)
# Right: Point chart (Gender x Confidence, filtered)
# =============================================================================

pisa_v1 = pisa_df[(pisa_df["HISCED"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["MATHEFF"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2]))].copy()

edu_map = {1: "Less than HS", 2: "Less than HS", 3: "High School",
           4: "Some College", 5: "Some College", 6: "Bachelor's",
           7: "Graduate+", 8: "Graduate+"}
pisa_v1["Parent_Education"] = pisa_v1["HISCED"].map(edu_map)
pisa_v1["Gender"] = pisa_v1["ST004D01T"].map({1: "Female", 2: "Male"})
pisa_v1["Confidence_Level"] = pd.qcut(pisa_v1["MATHEFF"], 3, labels = ["Low", "Medium", "High"])

heatmap_data = pisa_v1.groupby(["Parent_Education", "Confidence_Level"]).agg(
    Avg_Math = ("PV1MATH", "mean"),
    Count = ("PV1MATH", "count")
).reset_index()

driven_data = pisa_v1.groupby(["Parent_Education", "Gender", "Confidence_Level"]).agg(
    Avg_Math = ("PV1MATH", "mean"),
    Count = ("PV1MATH", "count")
).reset_index()

edu_order = ["Less than HS", "High School", "Some College", "Bachelor's", "Graduate+"]
conf_order = ["Low", "Medium", "High"]
edu_select = alt.selection_point(fields = ["Parent_Education"], name = "edu_select")

left_chart = alt.Chart(heatmap_data).mark_rect(cursor = "pointer").encode(
    x = alt.X("Confidence_Level:N", title = "Math Confidence", sort = conf_order),
    y = alt.Y("Parent_Education:N", title = "Parent Education", sort = edu_order),
    color = alt.Color("Avg_Math:Q",
                    scale = alt.Scale(scheme = "viridis", domain = [380, 540]),
                    legend = alt.Legend(title = "Avg Math Score")),
    opacity = alt.condition(edu_select, alt.value(1), alt.value(0.5)),
    tooltip = ["Parent_Education:N", "Confidence_Level:N",
             alt.Tooltip("Avg_Math:Q", format = ".1f", title = "Avg Math Score"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).add_params(edu_select).properties(
    name = "view_1",
    title = {"text": "Education x Confidence Heatmap", "subtitle": "Click row to filter by education",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 250, height = 280
)

right_chart = alt.Chart(driven_data).mark_point(
    filled = True, size = 150
).encode(
    y = alt.Y("Gender:N", title = None),
    yOffset = alt.YOffset("Confidence_Level:N", sort = conf_order),
    x = alt.X("Avg_Math:Q", title = "Average Math Score", scale = alt.Scale(domain = [380, 560])),
    color = alt.Color("Gender:N",
                    scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]),
                    legend = alt.Legend(title = "Gender", orient = "top")),
    shape = alt.Shape("Confidence_Level:N", legend = alt.Legend(title = "Confidence")),
    tooltip = ["Parent_Education:N", "Gender:N", "Confidence_Level:N",
             alt.Tooltip("Avg_Math:Q", format = ".1f"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).transform_filter(edu_select).properties(
    title = {"text": "Gender x Confidence", "color": "#FFFFFF", "fontSize": 14},
    width = 320, height = 280
)

viz1 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz1, "pisa_gender_efficacy_dumbbell.json")


# =============================================================================
# VIZ 2: Math Anxiety's Impact on Achievement by Gender
# Left: Heatmap (Anxiety x Gender -> Math Score)
# Right: Horizontal bar chart (Top 10 countries ranked)
# =============================================================================

pisa_v2 = pisa_df[(pisa_df["ANXMAT"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2]))].copy()
pisa_v2["Gender"] = pisa_v2["ST004D01T"].map({1: "Female", 2: "Male"})
pisa_v2["Anxiety_Level"] = pd.qcut(pisa_v2["ANXMAT"], 5,
    labels = ["Very Low", "Low", "Medium", "High", "Very High"])

heatmap_data = pisa_v2.groupby(["Anxiety_Level", "Gender"]).agg(
    Mean_Math = ("PV1MATH", "mean"),
    Count = ("PV1MATH", "count")
).reset_index()

country_names = {
    "SGP": "Singapore", "MAC": "Macao", "TWN": "Taiwan", "HKG": "Hong Kong",
    "JPN": "Japan", "KOR": "South Korea", "EST": "Estonia", "CHE": "Switzerland",
    "CAN": "Canada", "NLD": "Netherlands", "IRL": "Ireland", "BEL": "Belgium",
    "DNK": "Denmark", "GBR": "UK", "POL": "Poland", "AUT": "Austria",
    "AUS": "Australia", "CZE": "Czech Rep.", "SVN": "Slovenia", "FIN": "Finland"
}

top_countries = pisa_v2.groupby("CNT")["PV1MATH"].mean().nlargest(10).index.tolist()
country_data = pisa_v2[pisa_v2["CNT"].isin(top_countries)].groupby(
    ["CNT", "Anxiety_Level"]
).agg(Mean_Math = ("PV1MATH", "mean"), Count = ("PV1MATH", "count")).reset_index()
country_data["Country"] = country_data["CNT"].map(country_names).fillna(country_data["CNT"])

anxiety_order = ["Very Low", "Low", "Medium", "High", "Very High"]
anxiety_select = alt.selection_point(fields = ["Anxiety_Level"], name = "anxiety_select")

left_chart = alt.Chart(heatmap_data).mark_rect(cursor = "pointer").encode(
    x = alt.X("Gender:N", title = None),
    y = alt.Y("Anxiety_Level:N", title = "Math Anxiety Level", sort = anxiety_order),
    color = alt.Color("Mean_Math:Q",
                    scale = alt.Scale(scheme = "blues", domain = [420, 510]),
                    legend = alt.Legend(title = "Math Score")),
    opacity = alt.condition(anxiety_select, alt.value(1), alt.value(0.5)),
    tooltip = ["Anxiety_Level:N", "Gender:N",
             alt.Tooltip("Mean_Math:Q", format = ".1f", title = "Avg Math Score"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).add_params(anxiety_select).properties(
    name = "view_1",
    title = {"text": "Anxiety x Gender", "subtitle": "Click anxiety level to filter countries",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 180, height = 300
)

right_chart = alt.Chart(country_data).mark_bar(
    cornerRadiusTopRight = 4, cornerRadiusBottomRight = 4
).encode(
    y = alt.Y("Country:N", title = None, sort = alt.EncodingSortField(field = "Mean_Math", order = "descending")),
    x = alt.X("Mean_Math:Q", title = "Average Math Score", scale = alt.Scale(domain = [450, 600])),
    color = alt.Color("Mean_Math:Q",
                    scale = alt.Scale(scheme = "oranges", domain = [500, 580]),
                    legend = None),
    tooltip = ["Country:N", "Anxiety_Level:N",
             alt.Tooltip("Mean_Math:Q", format = ".1f"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).transform_filter(anxiety_select).properties(
    title = {"text": "Top 10 Countries Ranked", "color": "#FFFFFF", "fontSize": 14},
    width = 320, height = 300
)

viz2 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz2, "pisa_anxiety_performance_heatmap.json")


# =============================================================================
# VIZ 3: Global Math Achievement by Parent Education
# Left: World choropleth map (country math scores)
# Right: Line chart (education gap trend across countries)
# =============================================================================

pisa_v3 = pisa_df[(pisa_df["PV1MATH"].notna()) &
                   (pisa_df["HISCED"].notna())].copy()
pisa_v3["Parent_Education"] = pisa_v3["HISCED"].map(edu_map)

country_scores = pisa_v3.groupby("CNT").agg(
    Avg_Math = ("PV1MATH", "mean"),
    Count = ("PV1MATH", "count")
).reset_index()

country_id_map = {
    "ALB": 8, "ARE": 784, "ARG": 32, "AUS": 36, "AUT": 40, "BEL": 56, "BGR": 100,
    "BRA": 76, "CAN": 124, "CHE": 756, "CHL": 152, "COL": 170, "CRI": 188, "CZE": 203,
    "DEU": 276, "DNK": 208, "DOM": 214, "ESP": 724, "EST": 233, "FIN": 246, "FRA": 250,
    "GBR": 826, "GRC": 300, "HKG": 344, "HRV": 191, "HUN": 348, "IDN": 360, "IRL": 372,
    "ISL": 352, "ISR": 376, "ITA": 380, "JPN": 392, "KAZ": 398, "KOR": 410, "LTU": 440,
    "LUX": 442, "LVA": 428, "MAC": 446, "MEX": 484, "MYS": 458, "NLD": 528, "NOR": 578,
    "NZL": 554, "PER": 604, "PHL": 608, "POL": 616, "PRT": 620, "ROU": 642, "RUS": 643,
    "SAU": 682, "SGP": 702, "SRB": 688, "SVK": 703, "SVN": 705, "SWE": 752, "THA": 764,
    "TUR": 792, "TWN": 158, "UKR": 804, "URY": 858, "USA": 840, "VNM": 704
}

country_scores["id"] = country_scores["CNT"].map(country_id_map)
country_scores = country_scores[country_scores["id"].notna()]
country_scores["id"] = country_scores["id"].astype(int)

countries = alt.topo_feature(vega_data.world_110m.url, "countries")

country_select = alt.selection_point(fields = ["CNT"], name = "country_select")

background = alt.Chart(countries).mark_geoshape(
    fill = "#1a1a2e", stroke = "#333"
).project("equalEarth").properties(width = 450, height = 280)

choropleth = alt.Chart(countries).mark_geoshape(
    stroke = "#333", strokeWidth = 0.5
).encode(
    color = alt.condition(
        country_select,
        alt.Color("Avg_Math:Q", scale = alt.Scale(scheme = "viridis", domain = [350, 550]),
                legend = alt.Legend(title = "Math Score", orient = "bottom")),
        alt.value("#2a2a3e")
    ),
    tooltip = [alt.Tooltip("CNT:N", title = "Country"),
             alt.Tooltip("Avg_Math:Q", format = ".1f", title = "Avg Math"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).transform_lookup(
    lookup = "id",
    from_ = alt.LookupData(country_scores, "id", ["Avg_Math", "Count", "CNT"])
).project("equalEarth").add_params(country_select).properties(
    name = "view_1",
    title = {"text": "Global Math Scores (PISA 2022)", "subtitle": "Click country to see education gap",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 450, height = 280
)

left_chart = background + choropleth

edu_by_country = pisa_v3.groupby(["CNT", "Parent_Education"]).agg(
    Mean_Math = ("PV1MATH", "mean")
).reset_index()

top_10 = country_scores.nlargest(10, "Avg_Math")["CNT"].tolist()
edu_by_country = edu_by_country[edu_by_country["CNT"].isin(top_10)]
edu_by_country["Country"] = edu_by_country["CNT"].map(country_names).fillna(edu_by_country["CNT"])

right_chart = alt.Chart(edu_by_country).mark_line(
    point = {"filled": True, "size": 60}, strokeWidth = 2
).encode(
    x = alt.X("Parent_Education:O", title = "Parent Education", sort = edu_order),
    y = alt.Y("Mean_Math:Q", title = "Avg Math Score", scale = alt.Scale(domain = [400, 600])),
    color = alt.Color("Country:N",
                    scale = alt.Scale(scheme = "category10"),
                    legend = alt.Legend(title = "Country", orient = "right", columns = 1)),
    tooltip = ["Country:N", "Parent_Education:N",
             alt.Tooltip("Mean_Math:Q", format = ".1f")]
).transform_filter(country_select).properties(
    title = {"text": "Education Gap by Country", "color": "#FFFFFF", "fontSize": 14},
    width = 300, height = 280
)

viz3 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz3, "combined_immigration.json")


# =============================================================================
# VIZ 4: Family Income by Parent Education & Student Aspirations
# Left: Horizontal bar chart (income ranked by parent education)
# Right: Heatmap (STEM rate by Locale x Gender)
# =============================================================================

hsls_v4 = hsls_df[(hsls_df["X1PAR1EDU"].notna()) &
                   (hsls_df["X1FAMINCOME"].notna()) &
                   (hsls_df["X1SEX"].isin([1, 2])) &
                   (hsls_df["X1LOCALE"].notna())].copy()
hsls_v4 = hsls_v4[(hsls_v4["X1PAR1EDU"] > 0) & (hsls_v4["X1FAMINCOME"] > 0) & (hsls_v4["X1LOCALE"] > 0)]

hsls_edu_map = {1: "Less than HS", 2: "High School", 3: "Some College",
                4: "Some College", 5: "Bachelor's", 6: "Graduate+", 7: "Graduate+"}
hsls_v4["Parent_Education"] = hsls_v4["X1PAR1EDU"].map(hsls_edu_map)
hsls_v4["Gender"] = hsls_v4["X1SEX"].map({1: "Male", 2: "Female"})

income_map = {1: 7500, 2: 25000, 3: 45000, 4: 65000, 5: 85000, 6: 105000,
              7: 125000, 8: 145000, 9: 165000, 10: 185000, 11: 205000, 12: 225000, 13: 250000}
hsls_v4["Family_Income"] = hsls_v4["X1FAMINCOME"].map(income_map)

locale_map = {1: "City", 2: "Suburb", 3: "Town", 4: "Rural"}
hsls_v4["School_Locale"] = hsls_v4["X1LOCALE"].map(locale_map)

hsls_v4["STEM_Expect"] = hsls_v4["X1STU30OCC_STEM1"] == 1

income_data = hsls_v4.groupby("Parent_Education").agg(
    Avg_Income = ("Family_Income", "mean"),
    Count = ("Family_Income", "count")
).reset_index()

stem_heatmap = hsls_v4.groupby(["School_Locale", "Gender"]).agg(
    STEM_Rate = ("STEM_Expect", "mean"),
    Count = ("STEM_Expect", "count")
).reset_index()
stem_heatmap["STEM_Rate"] = stem_heatmap["STEM_Rate"] * 100

hsls_edu_order = ["Less than HS", "High School", "Some College", "Bachelor's", "Graduate+"]
locale_order = ["City", "Suburb", "Town", "Rural"]
edu_select = alt.selection_point(fields = ["Parent_Education"], name = "edu_select")

left_chart = alt.Chart(income_data).mark_bar(
    cornerRadiusTopRight = 4, cornerRadiusBottomRight = 4, cursor = "pointer"
).encode(
    y = alt.Y("Parent_Education:N", title = "Parent Education", sort = alt.EncodingSortField(field = "Avg_Income", order = "descending")),
    x = alt.X("Avg_Income:Q", title = "Average Family Income", axis = alt.Axis(format = "$,.0f")),
    color = alt.Color("Avg_Income:Q",
                    scale = alt.Scale(scheme = "greens", domain = [20000, 180000]),
                    legend = None),
    opacity = alt.condition(edu_select, alt.value(1), alt.value(0.4)),
    tooltip = ["Parent_Education:N",
             alt.Tooltip("Avg_Income:Q", format = "$,.0f", title = "Avg Income"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).add_params(edu_select).properties(
    name = "view_1",
    title = {"text": "Income by Parent Education", "subtitle": "Click to filter STEM rates",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 300, height = 280
)

stem_by_edu_locale = hsls_v4.groupby(["Parent_Education", "School_Locale", "Gender"]).agg(
    STEM_Rate = ("STEM_Expect", "mean"),
    Count = ("STEM_Expect", "count")
).reset_index()
stem_by_edu_locale["STEM_Rate"] = stem_by_edu_locale["STEM_Rate"] * 100

right_chart = alt.Chart(stem_by_edu_locale).mark_rect().encode(
    x = alt.X("Gender:N", title = None),
    y = alt.Y("School_Locale:N", title = "School Location", sort = locale_order),
    color = alt.Color("STEM_Rate:Q",
                    scale = alt.Scale(scheme = "purples", domain = [20, 50]),
                    legend = alt.Legend(title = "STEM %")),
    tooltip = ["Parent_Education:N", "School_Locale:N", "Gender:N",
             alt.Tooltip("STEM_Rate:Q", format = ".1f", title = "STEM Rate (%)"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).transform_filter(edu_select).properties(
    title = {"text": "STEM Rate by Locale x Gender", "color": "#FFFFFF", "fontSize": 14},
    width = 200, height = 280
)

viz4 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz4, "combined_gender_stem.json")


# =============================================================================
# VIZ 5: The STEM Pipeline - 9th Grade to College
# Left: Line chart (pipeline progression by gender)
# Right: Slope chart (conversion rate by parent education)
# =============================================================================

hsls_v5 = hsls_df[(hsls_df["X1SEX"].isin([1, 2])) &
                   (hsls_df["X1STU30OCC_STEM1"].notna()) &
                   (hsls_df["X4RFDGMJSTEM"].notna()) &
                   (hsls_df["X1PAR1EDU"].notna())].copy()
hsls_v5 = hsls_v5[hsls_v5["X1PAR1EDU"] > 0]

hsls_v5["Gender"] = hsls_v5["X1SEX"].map({1: "Male", 2: "Female"})
hsls_v5["Parent_Education"] = hsls_v5["X1PAR1EDU"].map(hsls_edu_map)
hsls_v5["STEM_9th"] = hsls_v5["X1STU30OCC_STEM1"] == 1
hsls_v5["STEM_Major"] = hsls_v5["X4RFDGMJSTEM"] == 1

if "X2STU30OCC_STEM1" in hsls_v5.columns:
    hsls_v5["STEM_11th"] = hsls_v5["X2STU30OCC_STEM1"] == 1
else:
    hsls_v5["STEM_11th"] = hsls_v5["STEM_9th"]

pipeline_rows = []
for stage, col in [("9th Grade", "STEM_9th"), ("11th Grade", "STEM_11th"), ("College Major", "STEM_Major")]:
    for gender in ["Female", "Male"]:
        subset = hsls_v5[hsls_v5["Gender"] == gender]
        rate = subset[col].mean() * 100
        count = len(subset)
        pipeline_rows.append({"Stage": stage, "Gender": gender, "STEM_Rate": rate, "Count": count})
pipeline_df = pd.DataFrame(pipeline_rows)

stage_order = ["9th Grade", "11th Grade", "College Major"]
stage_select = alt.selection_point(fields = ["Stage"], name = "stage_select")

left_chart = alt.Chart(pipeline_df).mark_line(
    point = {"filled": True, "size": 100}, strokeWidth = 3, cursor = "pointer"
).encode(
    x = alt.X("Stage:N", title = None, sort = stage_order),
    y = alt.Y("STEM_Rate:Q", title = "STEM Rate (%)", scale = alt.Scale(domain = [0, 50])),
    color = alt.Color("Gender:N",
                    scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]),
                    legend = alt.Legend(title = "Gender", orient = "top")),
    opacity = alt.condition(stage_select, alt.value(1), alt.value(0.4)),
    tooltip = ["Stage:N", "Gender:N",
             alt.Tooltip("STEM_Rate:Q", format = ".1f", title = "STEM Rate (%)"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).add_params(stage_select).properties(
    name = "view_1",
    title = {"text": "STEM Pipeline by Gender", "subtitle": "Click stage to see conversion",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 280, height = 320
)

stem_expecters = hsls_v5[hsls_v5["STEM_9th"] == True]
conversion_data = []
for edu in hsls_edu_order:
    subset = stem_expecters[stem_expecters["Parent_Education"] == edu]
    if len(subset) > 10:
        start_rate = 100
        end_rate = subset["STEM_Major"].mean() * 100
        conversion_data.append({"Parent_Education": edu, "Stage": "9th Grade Expectation", "Rate": start_rate, "Count": len(subset)})
        conversion_data.append({"Parent_Education": edu, "Stage": "College Major", "Rate": end_rate, "Count": len(subset)})
slope_df = pd.DataFrame(conversion_data)

right_chart = alt.Chart(slope_df).mark_line(
    point = {"filled": True, "size": 80}, strokeWidth = 2
).encode(
    x = alt.X("Stage:N", title = None, sort = ["9th Grade Expectation", "College Major"]),
    y = alt.Y("Rate:Q", title = "Conversion Rate (%)", scale = alt.Scale(domain = [0, 110])),
    color = alt.Color("Parent_Education:N",
                    scale = alt.Scale(domain = hsls_edu_order, scheme = "tableau10"),
                    legend = alt.Legend(title = "Parent Edu", orient = "right")),
    tooltip = ["Parent_Education:N", "Stage:N",
             alt.Tooltip("Rate:Q", format = ".1f", title = "Rate (%)"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).properties(
    title = {"text": "STEM Conversion: Expectation to Major", "subtitle": "Slope shows retention rate",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 280, height = 320
)

viz5 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz5, "hsls_math_identity_race.json")


# =============================================================================
# VIZ 6: Socioeconomic Pathways to STEM Majors
# Left: Line chart (GPA trajectory by SES)
# Right: Heatmap (STEM rate by SES x GPA Quartile)
# =============================================================================

hsls_v6 = hsls_df[(hsls_df["X1SESQ5"].notna()) &
                   (hsls_df["X3TGPA9TH"].notna()) &
                   (hsls_df["X3TGPA12TH"].notna()) &
                   (hsls_df["X4RFDGMJSTEM"].notna())].copy()
hsls_v6 = hsls_v6[(hsls_v6["X1SESQ5"] > 0) & (hsls_v6["X3TGPA9TH"] > 0) & (hsls_v6["X3TGPA12TH"] > 0)]

ses_labels = {1: "Lowest 20%", 2: "Second 20%", 3: "Middle 20%", 4: "Fourth 20%", 5: "Highest 20%"}
hsls_v6["SES_Quintile"] = hsls_v6["X1SESQ5"].map(ses_labels)
hsls_v6["STEM_Major"] = hsls_v6["X4RFDGMJSTEM"] == 1

gpa_cols = {"X3TGPA9TH": "9th", "X3TGPA10TH": "10th", "X3TGPA11TH": "11th", "X3TGPA12TH": "12th"}
gpa_rows = []
for col, grade in gpa_cols.items():
    if col in hsls_v6.columns:
        for ses in ["Lowest 20%", "Second 20%", "Middle 20%", "Fourth 20%", "Highest 20%"]:
            subset = hsls_v6[(hsls_v6["SES_Quintile"] == ses) & (hsls_v6[col] > 0)]
            if len(subset) > 0:
                gpa_rows.append({"Grade": grade, "SES_Quintile": ses, "GPA": subset[col].mean(), "Count": len(subset)})
gpa_df = pd.DataFrame(gpa_rows)

hsls_v6["GPA_Quartile"] = pd.qcut(hsls_v6["X3TGPA12TH"], 4, labels = ["Low", "Med-Low", "Med-High", "High"])

stem_ses_gpa = hsls_v6.groupby(["SES_Quintile", "GPA_Quartile"]).agg(
    STEM_Rate = ("STEM_Major", "mean"),
    Count = ("STEM_Major", "count")
).reset_index()
stem_ses_gpa["STEM_Rate"] = stem_ses_gpa["STEM_Rate"] * 100

ses_order = ["Lowest 20%", "Second 20%", "Middle 20%", "Fourth 20%", "Highest 20%"]
grade_order = ["9th", "10th", "11th", "12th"]
gpa_order = ["Low", "Med-Low", "Med-High", "High"]
ses_select = alt.selection_point(fields = ["SES_Quintile"], name = "ses_select")

left_chart = alt.Chart(gpa_df).mark_line(
    point = {"filled": True, "size": 80}, strokeWidth = 3, cursor = "pointer"
).encode(
    x = alt.X("Grade:N", title = "Grade Level", sort = grade_order),
    y = alt.Y("GPA:Q", title = "Average GPA", scale = alt.Scale(domain = [2.4, 3.4])),
    color = alt.Color("SES_Quintile:N",
                    scale = alt.Scale(domain = ses_order, scheme = "blues"),
                    legend = alt.Legend(title = "SES Quintile", orient = "top")),
    opacity = alt.condition(ses_select, alt.value(1), alt.value(0.3)),
    tooltip = ["SES_Quintile:N", "Grade:N",
             alt.Tooltip("GPA:Q", format = ".2f"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).add_params(ses_select).properties(
    name = "view_1",
    title = {"text": "GPA Trajectory by SES", "subtitle": "Click SES level to filter STEM rates",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 320, height = 320
)

right_chart = alt.Chart(stem_ses_gpa).mark_rect().encode(
    x = alt.X("GPA_Quartile:N", title = "GPA Quartile (12th Grade)", sort = gpa_order),
    y = alt.Y("SES_Quintile:N", title = "SES Quintile", sort = ses_order),
    color = alt.Color("STEM_Rate:Q",
                    scale = alt.Scale(scheme = "oranges", domain = [5, 35]),
                    legend = alt.Legend(title = "STEM %")),
    tooltip = ["SES_Quintile:N", "GPA_Quartile:N",
             alt.Tooltip("STEM_Rate:Q", format = ".1f", title = "STEM Rate (%)"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).transform_filter(ses_select).properties(
    title = {"text": "STEM Rate by SES x GPA", "color": "#FFFFFF", "fontSize": 14},
    width = 250, height = 320
)

viz6 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz6, "hsls_gpa_ses_trajectory.json")


# =============================================================================
# VIZ 7: Universal SES-Achievement Connection
# Left: Horizontal bar (PISA SES quintiles)
# Right: Horizontal bar (HSLS SES quintiles)
# =============================================================================

pisa_v7 = pisa_df[(pisa_df["ESCS"].notna()) &
                   (pisa_df["PV1MATH"].notna())].copy()
pisa_v7["SES_Quintile"] = pd.qcut(pisa_v7["ESCS"], 5, labels = ["Q1 (Lowest)", "Q2", "Q3", "Q4", "Q5 (Highest)"])

pisa_ses = pisa_v7.groupby("SES_Quintile").agg(
    Math_Score = ("PV1MATH", "mean"),
    Count = ("PV1MATH", "count")
).reset_index()

hsls_v7 = hsls_df[(hsls_df["X1SESQ5"].notna()) &
                   (hsls_df["X1TXMTSCOR"].notna())].copy()
hsls_v7 = hsls_v7[hsls_v7["X1SESQ5"] > 0]
hsls_v7["SES_Quintile"] = hsls_v7["X1SESQ5"].map({1: "Q1 (Lowest)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (Highest)"})

hsls_ses = hsls_v7.groupby("SES_Quintile").agg(
    Math_Score = ("X1TXMTSCOR", "mean"),
    Count = ("X1TXMTSCOR", "count")
).reset_index()

quintile_order = ["Q1 (Lowest)", "Q2", "Q3", "Q4", "Q5 (Highest)"]
ses_highlight = alt.selection_point(fields = ["SES_Quintile"], name = "ses_highlight")

left_chart = alt.Chart(pisa_ses).mark_bar(
    cornerRadiusTopRight = 4, cornerRadiusBottomRight = 4, cursor = "pointer"
).encode(
    y = alt.Y("SES_Quintile:O", title = "SES Quintile", sort = quintile_order),
    x = alt.X("Math_Score:Q", title = "Avg Math Score", scale = alt.Scale(domain = [380, 540])),
    color = alt.Color("Math_Score:Q",
                    scale = alt.Scale(scheme = "viridis", domain = [420, 520]),
                    legend = None),
    opacity = alt.condition(ses_highlight, alt.value(1), alt.value(0.4)),
    tooltip = ["SES_Quintile:N",
             alt.Tooltip("Math_Score:Q", format = ".1f"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).add_params(ses_highlight).properties(
    name = "view_1",
    title = {"text": "PISA (International)", "subtitle": "Click to compare with HSLS",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 280, height = 280
)

right_chart = alt.Chart(hsls_ses).mark_bar(
    cornerRadiusTopRight = 4, cornerRadiusBottomRight = 4
).encode(
    y = alt.Y("SES_Quintile:O", title = None, sort = quintile_order),
    x = alt.X("Math_Score:Q", title = "Avg Math Score", scale = alt.Scale(domain = [42, 58])),
    color = alt.Color("Math_Score:Q",
                    scale = alt.Scale(scheme = "viridis", domain = [45, 55]),
                    legend = None),
    opacity = alt.condition(ses_highlight, alt.value(1), alt.value(0.4)),
    tooltip = ["SES_Quintile:N",
             alt.Tooltip("Math_Score:Q", format = ".1f"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).properties(
    title = {"text": "HSLS (US)", "color": "#FFFFFF", "fontSize": 14},
    width = 280, height = 280
)

viz7 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz7, "combined_efficacy_comparison.json")


# =============================================================================
# VIZ 8: Math Confidence -> Performance Across Datasets
# Left: Heatmap (PISA: Confidence x Parent Education)
# Right: Heatmap (HSLS: Confidence x Parent Education)
# =============================================================================

pisa_v8 = pisa_df[(pisa_df["MATHEFF"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["HISCED"].notna())].copy()
pisa_v8["Confidence_Level"] = pd.qcut(pisa_v8["MATHEFF"], 3, labels = ["Low", "Medium", "High"])
pisa_v8["Parent_Education"] = pisa_v8["HISCED"].map({
    1: "Less than HS", 2: "Less than HS", 3: "HS+", 4: "HS+", 5: "HS+", 6: "College+", 7: "College+", 8: "College+"
})

pisa_heatmap = pisa_v8.groupby(["Confidence_Level", "Parent_Education"]).agg(
    Math_Score = ("PV1MATH", "mean"),
    Count = ("PV1MATH", "count")
).reset_index()

hsls_v8 = hsls_df[(hsls_df["X1MTHEFF"].notna()) &
                   (hsls_df["X1TXMTSCOR"].notna()) &
                   (hsls_df["X1PAR1EDU"].notna())].copy()
hsls_v8 = hsls_v8[hsls_v8["X1PAR1EDU"] > 0]
hsls_v8["Confidence_Level"] = pd.qcut(hsls_v8["X1MTHEFF"], 3, labels = ["Low", "Medium", "High"])
hsls_v8["Parent_Education"] = hsls_v8["X1PAR1EDU"].map({
    1: "Less than HS", 2: "HS+", 3: "HS+", 4: "HS+", 5: "College+", 6: "College+", 7: "College+"
})

hsls_heatmap = hsls_v8.groupby(["Confidence_Level", "Parent_Education"]).agg(
    Math_Score = ("X1TXMTSCOR", "mean"),
    Count = ("X1TXMTSCOR", "count")
).reset_index()

conf_order = ["Low", "Medium", "High"]
parent_edu_order_3 = ["Less than HS", "HS+", "College+"]
conf_highlight = alt.selection_point(fields = ["Confidence_Level"], name = "conf_highlight")

left_chart = alt.Chart(pisa_heatmap).mark_rect(cursor = "pointer").encode(
    x = alt.X("Parent_Education:N", title = "Parent Education", sort = parent_edu_order_3),
    y = alt.Y("Confidence_Level:N", title = "Math Confidence", sort = conf_order),
    color = alt.Color("Math_Score:Q",
                    scale = alt.Scale(scheme = "plasma", domain = [380, 540]),
                    legend = alt.Legend(title = "Math Score")),
    opacity = alt.condition(conf_highlight, alt.value(1), alt.value(0.5)),
    tooltip = ["Confidence_Level:N", "Parent_Education:N",
             alt.Tooltip("Math_Score:Q", format = ".1f"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).add_params(conf_highlight).properties(
    name = "view_1",
    title = {"text": "PISA (International)", "subtitle": "Click confidence to highlight",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 250, height = 220
)

right_chart = alt.Chart(hsls_heatmap).mark_rect().encode(
    x = alt.X("Parent_Education:N", title = "Parent Education", sort = parent_edu_order_3),
    y = alt.Y("Confidence_Level:N", title = None, sort = conf_order),
    color = alt.Color("Math_Score:Q",
                    scale = alt.Scale(scheme = "plasma", domain = [42, 56]),
                    legend = None),
    opacity = alt.condition(conf_highlight, alt.value(1), alt.value(0.5)),
    tooltip = ["Confidence_Level:N", "Parent_Education:N",
             alt.Tooltip("Math_Score:Q", format = ".1f"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).properties(
    title = {"text": "HSLS (US)", "color": "#FFFFFF", "fontSize": 14},
    width = 250, height = 220
)

viz8 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz8, "combined_ses_achievement.json")


# =============================================================================
# VIZ 9: Parent Education Premium Across 3 Datasets
# Left: Line chart (education-achievement link)
# Right: Horizontal bar (premium ranking)
# =============================================================================

hsls_v9 = hsls_df[(hsls_df["X1PAR1EDU"].notna()) & (hsls_df["X1TXMTSCOR"].notna())].copy()
hsls_v9 = hsls_v9[hsls_v9["X1PAR1EDU"] > 0]
hsls_v9["Parent_Education"] = hsls_v9["X1PAR1EDU"].map(hsls_edu_map)
hsls_agg = hsls_v9.groupby("Parent_Education").agg(Math_Score = ("X1TXMTSCOR", "mean")).reset_index()
hsls_agg["Source"] = "HSLS (US 2009)"

pisa_v9 = pisa_df[(pisa_df["HISCED"].notna()) & (pisa_df["PV1MATH"].notna())].copy()
pisa_v9["Parent_Education"] = pisa_v9["HISCED"].map(edu_map)

pisa_us = pisa_v9[pisa_v9["CNT"] == "USA"]
pisa_us_agg = pisa_us.groupby("Parent_Education").agg(Math_Score = ("PV1MATH", "mean")).reset_index()
pisa_us_agg["Source"] = "PISA US (2022)"

pisa_intl = pisa_v9[pisa_v9["CNT"] != "USA"]
pisa_intl_agg = pisa_intl.groupby("Parent_Education").agg(Math_Score = ("PV1MATH", "mean")).reset_index()
pisa_intl_agg["Source"] = "PISA Intl (2022)"

combined = pd.concat([hsls_agg, pisa_us_agg, pisa_intl_agg])

baseline = combined[combined["Parent_Education"] == "Less than HS"].set_index("Source")["Math_Score"].to_dict()
combined["Premium"] = combined.apply(lambda r: r["Math_Score"] - baseline.get(r["Source"], r["Math_Score"]), axis = 1)

source_order = ["HSLS (US 2009)", "PISA US (2022)", "PISA Intl (2022)"]
source_colors = ["#E69F00", "#56B4E9", "#009E73"]
edu_select = alt.selection_point(fields = ["Parent_Education"], name = "edu_select")

left_chart = alt.Chart(combined).mark_line(
    point = {"filled": True, "size": 80}, strokeWidth = 3, cursor = "pointer"
).encode(
    x = alt.X("Parent_Education:O", title = "Parent Education", sort = edu_order, axis = alt.Axis(labelAngle = -45)),
    y = alt.Y("Math_Score:Q", title = "Math Score (Raw Units)"),
    color = alt.Color("Source:N",
                    scale = alt.Scale(domain = source_order, range = source_colors),
                    legend = alt.Legend(title = "Data Source", orient = "top")),
    opacity = alt.condition(edu_select, alt.value(1), alt.value(0.3)),
    tooltip = ["Parent_Education:N", "Source:N",
             alt.Tooltip("Math_Score:Q", format = ".1f")]
).add_params(edu_select).properties(
    name = "view_1",
    title = {"text": "Education-Achievement Link", "subtitle": "Click education level to see premium",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 380, height = 320
)

right_chart = alt.Chart(combined).mark_bar(
    cornerRadiusTopRight = 4, cornerRadiusBottomRight = 4
).encode(
    y = alt.Y("Source:N", title = None, sort = source_order),
    x = alt.X("Premium:Q", title = "Score Premium vs Less than HS"),
    color = alt.Color("Source:N",
                    scale = alt.Scale(domain = source_order, range = source_colors),
                    legend = None),
    tooltip = ["Parent_Education:N", "Source:N",
             alt.Tooltip("Premium:Q", format = ".1f", title = "Premium")]
).transform_filter(edu_select).properties(
    title = {"text": "Education Premium", "color": "#FFFFFF", "fontSize": 14},
    width = 200, height = 320
)

viz9 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz9, "combined_parent_education.json")


# =============================================================================
# VERIFICATION
# =============================================================================

print("Generated JSON files:")
for f in sorted(OUTPUT_DIR.glob("*.json")):
    size = f.stat().st_size
    print(f"  {f.name}: {size:,} bytes")
