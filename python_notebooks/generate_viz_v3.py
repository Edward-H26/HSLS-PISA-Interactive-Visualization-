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
# VIZ 1: Global Comparison of PISA Scores by Domain
# Left: Dot plot (Top 15 countries by domain, brush selection)
# Right: Horizontal bar chart (Global averages filtered by brush)
# =============================================================================

score_cols = {"PV1MATH": "MATH", "PV1READ": "READ", "PV1SCIE": "SCIE"}
rankings_list = []
for col, domain in score_cols.items():
    country_means = pisa_df.groupby("CNT")[col].mean().reset_index()
    country_means.columns = ["Country", "Mean"]
    country_means["Domain"] = domain
    country_means["Rank"] = country_means["Mean"].rank(ascending = False)
    rankings_list.append(country_means)
rankings_df = pd.concat(rankings_list, ignore_index = True)

top_countries_list = []
for domain in ["MATH", "READ", "SCIE"]:
    domain_top = rankings_df[rankings_df["Domain"] == domain].nsmallest(15, "Rank").copy()
    top_countries_list.append(domain_top)
rankings_top15 = pd.concat(top_countries_list, ignore_index = True)

domain_avg = rankings_top15.groupby("Domain").agg(
    Avg_Score = ("Mean", "mean"),
    N_Countries = ("Country", "count")
).reset_index()

brush_domain = alt.selection_interval(encodings = ["x"], name = "domain_brush")

left_chart = alt.Chart(rankings_top15).mark_circle(size = 80, cursor = "crosshair").encode(
    x = alt.X("Country:N",
             sort = alt.EncodingSortField(field = "Mean", order = "descending"),
             title = "Country",
             axis = alt.Axis(labelAngle = -45, labelFontSize = 9, titleFontSize = 12)),
    y = alt.Y("Mean:Q", title = "Score", scale = alt.Scale(domain = [480, 580])),
    color = alt.condition(
        brush_domain,
        alt.Color("Domain:N", title = "Domain",
                 scale = alt.Scale(domain = ["MATH", "READ", "SCIE"],
                                 range = ["#1f77b4", "#2ca02c", "#d62728"]),
                 legend = alt.Legend(titleFontSize = 12, labelFontSize = 11, orient = "top")),
        alt.value("lightgray")
    ),
    tooltip = [alt.Tooltip("Country:N", title = "Country"),
              alt.Tooltip("Domain:N", title = "Domain"),
              alt.Tooltip("Mean:Q", title = "Score", format = ".1f"),
              alt.Tooltip("Rank:Q", title = "Rank", format = ".0f")]
).add_params(brush_domain).properties(
    name = "view_1",
    width = 500, height = 350,
    title = {"text": "Top 15 Countries by Domain",
            "subtitle": "Drag to brush select countries",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0", "fontWeight": "bold"}
)

right_chart = alt.Chart(rankings_top15).mark_bar(cornerRadius = 4).encode(
    y = alt.Y("Domain:N", title = "Domain"),
    x = alt.X("mean(Mean):Q", title = "Average Score", scale = alt.Scale(domain = [480, 560])),
    color = alt.Color("Domain:N",
                    scale = alt.Scale(domain = ["MATH", "READ", "SCIE"],
                                    range = ["#1f77b4", "#2ca02c", "#d62728"]),
                    legend = None),
    tooltip = [alt.Tooltip("Domain:N", title = "Domain"),
              alt.Tooltip("mean(Mean):Q", title = "Average", format = ".1f"),
              alt.Tooltip("count():Q", title = "Countries")]
).transform_filter(brush_domain).properties(
    width = 250, height = 150,
    title = {"text": "Selected Countries Average", "color": "#FFFFFF", "fontSize": 14, "fontWeight": "bold"}
)

viz1 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz1, "pisa_gender_efficacy_dumbbell.json")


# =============================================================================
# VIZ 2: Gender Gap in Math Self-Efficacy Across Countries
# Left: Diverging bar chart (Gap by country, sorted)
# Right: Paired dot plot (Efficacy & Anxiety for selected country)
# =============================================================================

pisa_v2 = pisa_df[(pisa_df["MATHEFF"].notna()) &
                   (pisa_df["ANXMAT"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2]))].copy()
pisa_v2["Gender"] = pisa_v2["ST004D01T"].map({1: "Female", 2: "Male"})

pisa_gender = pisa_v2.groupby(["CNT", "Gender"]).agg(
    MATHEFF = ("MATHEFF", "mean"),
    ANXMAT = ("ANXMAT", "mean")
).reset_index()

country_names_v2 = {
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

pivot_eff = pisa_gender.pivot(index = "CNT", columns = "Gender", values = "MATHEFF").reset_index()
pivot_eff["Gap"] = pivot_eff["Male"] - pivot_eff["Female"]
pivot_eff["Country"] = pivot_eff["CNT"].map(country_names_v2).fillna(pivot_eff["CNT"])
pivot_eff = pivot_eff.sort_values("Gap", ascending = False)

detail_data = pisa_gender.melt(
    id_vars = ["CNT", "Gender"],
    value_vars = ["MATHEFF", "ANXMAT"],
    var_name = "Measure",
    value_name = "Score"
)
detail_data["Measure"] = detail_data["Measure"].map({"MATHEFF": "Self-Efficacy", "ANXMAT": "Anxiety"})
detail_data["Country"] = detail_data["CNT"].map(country_names_v2).fillna(detail_data["CNT"])

click_country = alt.selection_point(fields = ["CNT"], empty = True, name = "country_select")

left_chart = alt.Chart(pivot_eff).mark_bar(cornerRadius = 3, cursor = "pointer").encode(
    y = alt.Y("Country:N", title = None,
             sort = alt.EncodingSortField(field = "Gap", order = "descending"),
             axis = alt.Axis(labelFontSize = 10)),
    x = alt.X("Gap:Q", title = "Gender Gap (Male - Female)",
             scale = alt.Scale(domain = [-0.4, 0.4])),
    color = alt.condition(
        alt.datum.Gap > 0,
        alt.value("#1976D2"),
        alt.value("#E91E63")
    ),
    opacity = alt.condition(click_country, alt.value(1.0), alt.value(0.7)),
    tooltip = [alt.Tooltip("Country:N", title = "Country"),
              alt.Tooltip("Gap:Q", title = "Gap", format = "+.3f"),
              alt.Tooltip("Male:Q", title = "Male Score", format = ".3f"),
              alt.Tooltip("Female:Q", title = "Female Score", format = ".3f")]
).add_params(click_country).properties(
    name = "view_1",
    title = {"text": "Gender Gap in Math Self-Efficacy",
            "subtitle": "Blue = Male higher, Pink = Female higher. Click to explore.",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 350, height = 500
)

dots = alt.Chart(detail_data).mark_point(size = 120, filled = True).encode(
    y = alt.Y("Measure:N", title = None, axis = alt.Axis(labelFontSize = 12)),
    x = alt.X("Score:Q", title = "Score", scale = alt.Scale(domain = [-0.5, 0.5])),
    color = alt.Color("Gender:N",
                     scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]),
                     legend = alt.Legend(title = "Gender", orient = "top")),
    tooltip = [alt.Tooltip("Country:N"),
              alt.Tooltip("Measure:N"),
              alt.Tooltip("Gender:N"),
              alt.Tooltip("Score:Q", format = ".3f")]
).transform_filter(click_country)

lines = alt.Chart(detail_data).mark_rule(strokeWidth = 2, opacity = 0.5).encode(
    y = alt.Y("Measure:N"),
    x = alt.X("min(Score):Q"),
    x2 = alt.X2("max(Score):Q")
).transform_filter(click_country)

right_chart = (lines + dots).properties(
    title = {"text": "Efficacy vs Anxiety by Gender",
            "subtitle": "Selected country comparison",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 300, height = 150
)

viz2 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz2, "pisa_anxiety_performance_heatmap.json")


# =============================================================================
# VIZ 3: Global Math Achievement by Parent Education
# Left: World choropleth map (country math scores)
# Right: Line chart (education gap trend across countries)
# =============================================================================

edu_map = {0: "None", 1: "Primary", 2: "Lower Secondary", 3: "Upper Secondary",
           4: "Post-Secondary", 5: "Tertiary", 6: "Graduate+"}
edu_order = ["None", "Primary", "Lower Secondary", "Upper Secondary",
             "Post-Secondary", "Tertiary", "Graduate+"]

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
edu_by_country["Country"] = edu_by_country["CNT"].map(country_names_v2).fillna(edu_by_country["CNT"])

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
# VIZ 4: SES Achievement Gap & STEM Interests
# Left: Vertical bar chart (Math Achievement by SES Quintile)
# Right: Heatmap (GPA by Math Interest x Science Interest)
# =============================================================================

hsls_v4 = hsls_df[(hsls_df["X1SESQ5"].notna()) &
                   (hsls_df["X1TXMTSCOR"].notna()) &
                   (hsls_df["X1MTHID"].notna()) &
                   (hsls_df["X1SCIID"].notna()) &
                   (hsls_df["X3TGPA12TH"].notna())].copy()
hsls_v4 = hsls_v4[(hsls_v4["X1SESQ5"] > 0) & (hsls_v4["X1MTHID"] > -5) & (hsls_v4["X1SCIID"] > -5)]

ses_labels = {1: "Q1 (Lowest 20%)", 2: "Q2 (Second 20%)", 3: "Q3 (Middle 20%)",
              4: "Q4 (Fourth 20%)", 5: "Q5 (Highest 20%)"}
hsls_v4["SES_Quintile"] = hsls_v4["X1SESQ5"].map(ses_labels)

mth_terciles = hsls_v4["X1MTHID"].quantile([0, 0.33, 0.67, 1]).values
sci_terciles = hsls_v4["X1SCIID"].quantile([0, 0.33, 0.67, 1]).values
hsls_v4["Math_Interest"] = pd.cut(hsls_v4["X1MTHID"], bins = mth_terciles, labels = ["Low", "Medium", "High"], include_lowest = True)
hsls_v4["Science_Interest"] = pd.cut(hsls_v4["X1SCIID"], bins = sci_terciles, labels = ["Low", "Medium", "High"], include_lowest = True)

ses_data = hsls_v4.groupby("SES_Quintile").agg(
    Math_Score = ("X1TXMTSCOR", "mean"),
    Count = ("X1TXMTSCOR", "count")
).reset_index()

interest_gpa = hsls_v4.groupby(["SES_Quintile", "Math_Interest", "Science_Interest"]).agg(
    Avg_GPA = ("X3TGPA12TH", "mean"),
    Count = ("X3TGPA12TH", "count")
).reset_index()

ses_order = ["Q1 (Lowest 20%)", "Q2 (Second 20%)", "Q3 (Middle 20%)", "Q4 (Fourth 20%)", "Q5 (Highest 20%)"]
interest_order = ["Low", "Medium", "High"]
ses_select = alt.selection_point(fields = ["SES_Quintile"], name = "ses_select")

left_chart = alt.Chart(ses_data).mark_bar(
    cornerRadiusTopLeft = 4, cornerRadiusTopRight = 4, cursor = "pointer"
).encode(
    x = alt.X("SES_Quintile:N", title = "SES Quintile", sort = ses_order),
    y = alt.Y("Math_Score:Q", title = "Avg Math Score", scale = alt.Scale(domain = [44, 56])),
    color = alt.Color("Math_Score:Q",
                    scale = alt.Scale(scheme = "blues", domain = [44, 56]),
                    legend = None),
    opacity = alt.condition(ses_select, alt.value(1), alt.value(0.4)),
    tooltip = ["SES_Quintile:N",
             alt.Tooltip("Math_Score:Q", format = ".1f", title = "Avg Math Score"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).add_params(ses_select).properties(
    name = "view_1",
    title = {"text": "Math Achievement by SES", "subtitle": "Click to filter interest heatmap",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 280, height = 280
)

right_chart = alt.Chart(interest_gpa).mark_rect().encode(
    x = alt.X("Science_Interest:N", title = "Science Interest", sort = interest_order),
    y = alt.Y("Math_Interest:N", title = "Math Interest", sort = interest_order),
    color = alt.Color("Avg_GPA:Q",
                    scale = alt.Scale(scheme = "viridis", domain = [2.2, 3.4]),
                    legend = alt.Legend(title = "Avg GPA")),
    tooltip = ["SES_Quintile:N", "Math_Interest:N", "Science_Interest:N",
             alt.Tooltip("Avg_GPA:Q", format = ".2f", title = "Avg GPA"),
             alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).transform_filter(ses_select).properties(
    title = {"text": "GPA by Math & Science Interest", "color": "#FFFFFF", "fontSize": 14},
    width = 220, height = 280
)

viz4 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz4, "combined_gender_stem.json")


# =============================================================================
# VIZ 5: Parent Education, Student Aspirations & STEM Expectations
# Left: Grouped bar chart (income by parent edu + student expectations)
# Right: Horizontal grouped bar (STEM rate by locale + gender)
# =============================================================================

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
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 450, height = 350
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
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 380, height = 350
)

viz5 = alt.hconcat(left_chart, right_chart).resolve_scale(color = "independent")
save_chart(viz5, "hsls_math_identity_race.json")


# =============================================================================
# VIZ 6: Geographic Regional Distribution of STEM Major Selection with GPA Trajectories
# Left: US Choropleth Map (STEM counts by region)
# Right: Multi-line chart (GPA by race/ethnicity)
# =============================================================================

race_map_v6 = {
    1: "Am. Indian/Alaska Native", 1.0: "Am. Indian/Alaska Native",
    2: "Asian", 2.0: "Asian",
    3: "Black/African American", 3.0: "Black/African American",
    4: "Hispanic", 4.0: "Hispanic",
    5: "More than one race", 5.0: "More than one race",
    6: "Native Hawaiian/Pacific Islander", 6.0: "Native Hawaiian/Pacific Islander",
    7: "White", 7.0: "White"
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
                   (hsls_df["X4RFDGMJSTEM"].notna())].copy()

hsls_v6["race"] = hsls_v6["X1RACE"].map(race_map_v6).fillna("Unknown")
hsls_v6["is_stem_major"] = hsls_v6["X4RFDGMJSTEM"].map({0: 0, 0.0: 0, 1: 1, 1.0: 1})

if "X1CNTRL" in hsls_v6.columns:
    region_mapping = {
        1: "Northeast", 2: "Midwest", 3: "South", 4: "West"
    }
    hsls_v6["region"] = hsls_v6["X1CNTRL"].map(region_mapping).fillna("Unknown")
elif "X1REGION" in hsls_v6.columns:
    region_mapping = {1: "Northeast", 2: "Midwest", 3: "South", 4: "West"}
    hsls_v6["region"] = hsls_v6["X1REGION"].map(region_mapping).fillna("Unknown")
else:
    hsls_v6["region"] = "Unknown"

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
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 475, height = 350
)

gpa_cols_v6 = [("9th Grade", "X3TGPA9TH"), ("10th Grade", "X3TGPA10TH"),
               ("11th Grade", "X3TGPA11TH"), ("12th Grade", "X3TGPA12TH")]
gpa_frames = []
for label, col in gpa_cols_v6:
    if col in hsls_v6.columns:
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

gpa_agg = gpa_long.groupby(["region", "race", "grade"]).agg(
    avg_gpa = ("gpa", "mean"),
    count = ("gpa", "count")
).reset_index()

gpa_line = alt.Chart(gpa_agg).transform_filter(click_region).mark_line(
    point = alt.OverlayMarkDef(filled = True, size = 60), strokeWidth = 2.5
).encode(
    x = alt.X("grade:O", title = "Grade Level",
             sort = ["9th Grade", "10th Grade", "11th Grade", "12th Grade"],
             axis = alt.Axis(labelFontSize = 12, labelPadding = 10, titleFontSize = 14,
                           titleColor = "#FFFFFF", labelColor = "#E0E0E0", labelAngle = -45)),
    y = alt.Y("avg_gpa:Q", title = "Average GPA", scale = alt.Scale(domain = [2.0, 3.5]),
             axis = alt.Axis(format = ".2f", labelFontSize = 14, titleFontSize = 14,
                           titleColor = "#FFFFFF", labelColor = "#E0E0E0")),
    color = alt.Color("race:N", title = "Race/Ethnicity", sort = RACE_ORDER,
                     scale = alt.Scale(domain = RACE_ORDER, range = RACE_COLORS),
                     legend = alt.Legend(titleFontSize = 11, labelFontSize = 10, orient = "bottom",
                                        direction = "horizontal", columns = 4, symbolSize = 80,
                                        padding = 8, offset = 10, titlePadding = 8, labelLimit = 150)),
    tooltip = [alt.Tooltip("race:N", title = "Race/Ethnicity"),
              alt.Tooltip("grade:O", title = "Grade"),
              alt.Tooltip("avg_gpa:Q", title = "Average GPA", format = ".2f"),
              alt.Tooltip("count:Q", title = "Students", format = ",d")]
).properties(
    title = {"text": "GPA Trajectories by Race/Ethnicity (9th-12th Grade)",
            "subtitle": "Average GPA progression filtered by selected region",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 400, height = 350
)

viz6 = alt.hconcat(geo_map, gpa_line).resolve_scale(color = "independent")
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

hsls_edu_map = {1: "Less than HS", 2: "High School", 3: "Some College",
                4: "Some College", 5: "Bachelor's", 6: "Graduate+", 7: "Graduate+"}

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
