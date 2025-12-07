import pandas as pd
import altair as alt
from pathlib import Path
import json
import numpy as np

DATA_DIR = Path("../data")
OUTPUT_DIR = Path("../assets/json")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory=False)
hsls_df = pd.read_csv(DATA_DIR / "hsls_subset.csv", low_memory=False)

print(f"PISA: {len(pisa_df)} rows, {len(pisa_df.columns)} columns")
print(f"HSLS: {len(hsls_df)} rows, {len(hsls_df.columns)} columns")

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

def save_chart(chart, filename):
    spec = json.loads(chart.to_json())
    spec["config"] = DARK_CONFIG
    with open(OUTPUT_DIR / filename, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"Saved: {filename}")


print("\n" + "="*60)
print("VIZ 1: Parental Education Strongly Predicts Math Achievement")
print("="*60)

pisa_edu = pisa_df[(pisa_df["HISCED"].notna()) &
                    (pisa_df["PV1MATH"].notna()) &
                    (pisa_df["ST004D01T"].isin([1, 2]))].copy()

edu_map = {1: "Less than HS", 2: "Less than HS", 3: "High School",
           4: "Some College", 5: "Some College", 6: "Bachelor's",
           7: "Graduate+", 8: "Graduate+"}
pisa_edu["Parent_Education"] = pisa_edu["HISCED"].map(edu_map)
pisa_edu["Gender"] = pisa_edu["ST004D01T"].map({1: "Female", 2: "Male"})

driver_data = pisa_edu.groupby("Parent_Education").agg(
    Avg_Math=("PV1MATH", "mean"),
    Count=("PV1MATH", "count")
).reset_index()

driven_data = pisa_edu.groupby(["Parent_Education", "Gender"]).agg(
    Avg_Math=("PV1MATH", "mean"),
    Count=("PV1MATH", "count")
).reset_index()

edu_order = ["Less than HS", "High School", "Some College", "Bachelor's", "Graduate+"]
edu_select = alt.selection_point(fields=["Parent_Education"], name="edu_select")

left_chart = alt.Chart(driver_data).mark_bar(
    cornerRadiusTopRight=4, cornerRadiusBottomRight=4, cursor="pointer"
).encode(
    y=alt.Y("Parent_Education:N", title="Parent Education Level", sort=edu_order),
    x=alt.X("Avg_Math:Q", title="Average Math Score", scale=alt.Scale(domain=[400, 550])),
    color=alt.Color("Parent_Education:N",
                    scale=alt.Scale(domain=edu_order, scheme="blues"),
                    legend=None),
    opacity=alt.condition(edu_select, alt.value(1), alt.value(0.3)),
    tooltip=["Parent_Education:N", alt.Tooltip("Avg_Math:Q", format=".1f"),
             alt.Tooltip("Count:Q", format=",d", title="Students")]
).add_params(edu_select).properties(
    name="view_1",
    title={"text": "Click Education Level", "color": "#FFFFFF", "fontSize": 14},
    width=400, height=300
)

right_chart = alt.Chart(driven_data).mark_bar(
    cornerRadiusTopLeft=4, cornerRadiusTopRight=4
).encode(
    x=alt.X("Gender:N", title=None),
    y=alt.Y("Avg_Math:Q", title="Average Math Score", scale=alt.Scale(domain=[400, 550])),
    color=alt.Color("Gender:N",
                    scale=alt.Scale(domain=["Female", "Male"], range=["#E91E63", "#1976D2"]),
                    legend=alt.Legend(title="Gender", orient="top")),
    tooltip=["Parent_Education:N", "Gender:N", alt.Tooltip("Avg_Math:Q", format=".1f"),
             alt.Tooltip("Count:Q", format=",d", title="Students")]
).transform_filter(edu_select).properties(
    title={"text": "Gender Breakdown", "color": "#FFFFFF", "fontSize": 14},
    width=200, height=300
)

viz1 = alt.hconcat(left_chart, right_chart).resolve_scale(color="independent")
save_chart(viz1, "pisa_gender_efficacy_dumbbell.json")


print("\n" + "="*60)
print("VIZ 2: Math Anxiety is a Barrier to Achievement")
print("="*60)

pisa_anxiety = pisa_df[(pisa_df["ANXMAT"].notna()) &
                        (pisa_df["PV1MATH"].notna()) &
                        (pisa_df["ST004D01T"].isin([1, 2]))].copy()
pisa_anxiety["Gender"] = pisa_anxiety["ST004D01T"].map({1: "Female", 2: "Male"})
pisa_anxiety["Anxiety_Level"] = pd.qcut(pisa_anxiety["ANXMAT"], 5,
    labels=["Very Low", "Low", "Medium", "High", "Very High"])

driver_data = pisa_anxiety.groupby("Anxiety_Level").agg(
    Avg_Math=("PV1MATH", "mean"),
    Count=("PV1MATH", "count")
).reset_index()

driven_data = pisa_anxiety.groupby(["Anxiety_Level", "Gender"]).agg(
    Avg_Math=("PV1MATH", "mean")
).reset_index()

anxiety_order = ["Very Low", "Low", "Medium", "High", "Very High"]
anxiety_select = alt.selection_point(fields=["Anxiety_Level"], name="anxiety_select")

left_chart = alt.Chart(driver_data).mark_bar(
    cornerRadiusTopLeft=4, cornerRadiusTopRight=4, cursor="pointer"
).encode(
    x=alt.X("Anxiety_Level:N", title="Math Anxiety Level", sort=anxiety_order),
    y=alt.Y("Avg_Math:Q", title="Average Math Score", scale=alt.Scale(domain=[400, 520])),
    color=alt.Color("Anxiety_Level:N",
                    scale=alt.Scale(domain=anxiety_order, scheme="reds"),
                    legend=None),
    opacity=alt.condition(anxiety_select, alt.value(1), alt.value(0.3)),
    tooltip=["Anxiety_Level:N", alt.Tooltip("Avg_Math:Q", format=".1f"),
             alt.Tooltip("Count:Q", format=",d", title="Students")]
).add_params(anxiety_select).properties(
    name="view_1",
    title={"text": "Click Anxiety Level", "color": "#FFFFFF", "fontSize": 14},
    width=350, height=300
)

right_chart = alt.Chart(driven_data).mark_line(
    point={"filled": True, "size": 80}, strokeWidth=3
).encode(
    x=alt.X("Anxiety_Level:N", title="Math Anxiety Level", sort=anxiety_order),
    y=alt.Y("Avg_Math:Q", title="Average Math Score", scale=alt.Scale(domain=[400, 520])),
    color=alt.Color("Gender:N",
                    scale=alt.Scale(domain=["Female", "Male"], range=["#E91E63", "#1976D2"]),
                    legend=alt.Legend(title="Gender", orient="top")),
    tooltip=["Anxiety_Level:N", "Gender:N", alt.Tooltip("Avg_Math:Q", format=".1f")]
).properties(
    title={"text": "Gender Comparison", "color": "#FFFFFF", "fontSize": 14},
    width=350, height=300
)

viz2 = alt.hconcat(left_chart, right_chart).resolve_scale(color="independent")
save_chart(viz2, "pisa_anxiety_performance_heatmap.json")


print("\n" + "="*60)
print("VIZ 3: Top 15 Countries in Math Achievement")
print("="*60)

pisa_country = pisa_df[(pisa_df["PV1MATH"].notna()) &
                        (pisa_df["ST004D01T"].isin([1, 2]))].copy()
pisa_country["Gender"] = pisa_country["ST004D01T"].map({1: "Female", 2: "Male"})

country_means = pisa_country.groupby("CNT")["PV1MATH"].mean().nlargest(15)
top_countries = country_means.index.tolist()

country_names = {
    "SGP": "Singapore", "MAC": "Macao", "TWN": "Taiwan", "HKG": "Hong Kong",
    "JPN": "Japan", "KOR": "South Korea", "EST": "Estonia", "CHE": "Switzerland",
    "CAN": "Canada", "NLD": "Netherlands", "IRL": "Ireland", "BEL": "Belgium",
    "DNK": "Denmark", "GBR": "United Kingdom", "POL": "Poland", "AUT": "Austria",
    "AUS": "Australia", "CZE": "Czech Republic", "SVN": "Slovenia", "FIN": "Finland"
}

driver_data = pisa_country[pisa_country["CNT"].isin(top_countries)].groupby("CNT").agg(
    Avg_Math=("PV1MATH", "mean"),
    Count=("PV1MATH", "count")
).reset_index()
driver_data["Country"] = driver_data["CNT"].map(country_names)
driver_data["Country"] = driver_data["Country"].fillna(driver_data["CNT"])

driven_data = pisa_country[pisa_country["CNT"].isin(top_countries)].groupby(["CNT", "Gender"]).agg(
    Avg_Math=("PV1MATH", "mean")
).reset_index()
driven_data["Country"] = driven_data["CNT"].map(country_names)
driven_data["Country"] = driven_data["Country"].fillna(driven_data["CNT"])

country_select = alt.selection_point(fields=["Country"], name="country_select")

left_chart = alt.Chart(driver_data).mark_bar(
    cornerRadiusTopRight=4, cornerRadiusBottomRight=4, cursor="pointer"
).encode(
    y=alt.Y("Country:N", title=None, sort=alt.EncodingSortField(field="Avg_Math", order="descending")),
    x=alt.X("Avg_Math:Q", title="Average Math Score", scale=alt.Scale(domain=[450, 600])),
    color=alt.value("#26a69a"),
    opacity=alt.condition(country_select, alt.value(1), alt.value(0.3)),
    tooltip=["Country:N", alt.Tooltip("Avg_Math:Q", format=".1f"),
             alt.Tooltip("Count:Q", format=",d", title="Students")]
).add_params(country_select).properties(
    name="view_1",
    title={"text": "Click Country", "color": "#FFFFFF", "fontSize": 14},
    width=400, height=350
)

right_chart = alt.Chart(driven_data).mark_bar(
    cornerRadiusTopLeft=4, cornerRadiusTopRight=4
).encode(
    x=alt.X("Gender:N", title=None),
    y=alt.Y("Avg_Math:Q", title="Average Math Score", scale=alt.Scale(domain=[450, 600])),
    color=alt.Color("Gender:N",
                    scale=alt.Scale(domain=["Female", "Male"], range=["#E91E63", "#1976D2"]),
                    legend=alt.Legend(title="Gender", orient="top")),
    tooltip=["Country:N", "Gender:N", alt.Tooltip("Avg_Math:Q", format=".1f")]
).transform_filter(country_select).properties(
    title={"text": "Gender Gap", "color": "#FFFFFF", "fontSize": 14},
    width=200, height=350
)

viz3 = alt.hconcat(left_chart, right_chart).resolve_scale(color="independent")
save_chart(viz3, "combined_immigration.json")


print("\n" + "="*60)
print("VIZ 4: Family Background Shapes Academic Trajectories")
print("="*60)

hsls_gpa = hsls_df[(hsls_df["X1PAR1EDU"].notna()) &
                    (hsls_df["X3TGPA9TH"].notna()) &
                    (hsls_df["X3TGPA12TH"].notna())].copy()
hsls_gpa = hsls_gpa[(hsls_gpa["X1PAR1EDU"] > 0) & (hsls_gpa["X3TGPA9TH"] > 0) & (hsls_gpa["X3TGPA12TH"] > 0)]

edu_map = {1: "Less than HS", 2: "High School", 3: "Some College",
           4: "Some College", 5: "Bachelor's+", 6: "Bachelor's+", 7: "Bachelor's+"}
hsls_gpa["Parent_Education"] = hsls_gpa["X1PAR1EDU"].map(edu_map)

gpa_cols = {"X3TGPA9TH": "9th Grade", "X3TGPA10TH": "10th Grade",
            "X3TGPA11TH": "11th Grade", "X3TGPA12TH": "12th Grade"}

line_data = []
for edu in ["Less than HS", "High School", "Some College", "Bachelor's+"]:
    subset = hsls_gpa[hsls_gpa["Parent_Education"] == edu]
    for col, label in gpa_cols.items():
        if col in subset.columns:
            valid = subset[subset[col] > 0][col]
            if len(valid) > 0:
                line_data.append({
                    "Parent_Education": edu,
                    "Grade": label,
                    "GPA": valid.mean(),
                    "Count": len(valid)
                })
line_df = pd.DataFrame(line_data)

bar_data = hsls_gpa.groupby("Parent_Education").agg(
    GPA=("X3TGPA12TH", "mean"),
    Count=("X3TGPA12TH", "count")
).reset_index()

edu_order = ["Less than HS", "High School", "Some College", "Bachelor's+"]
grade_order = ["9th Grade", "10th Grade", "11th Grade", "12th Grade"]
edu_select = alt.selection_point(fields=["Parent_Education"], name="edu_select")

left_chart = alt.Chart(line_df).mark_line(
    point={"filled": True, "size": 80}, strokeWidth=3, cursor="pointer"
).encode(
    x=alt.X("Grade:N", title="Grade Level", sort=grade_order),
    y=alt.Y("GPA:Q", title="Average GPA", scale=alt.Scale(domain=[2.5, 3.5])),
    color=alt.Color("Parent_Education:N",
                    scale=alt.Scale(domain=edu_order, scheme="viridis"),
                    legend=alt.Legend(title="Parent Education", orient="top")),
    opacity=alt.condition(edu_select, alt.value(1), alt.value(0.3)),
    tooltip=["Parent_Education:N", "Grade:N", alt.Tooltip("GPA:Q", format=".2f")]
).add_params(edu_select).properties(
    name="view_1",
    title={"text": "Click Education Level", "color": "#FFFFFF", "fontSize": 14},
    width=400, height=300
)

right_chart = alt.Chart(bar_data).mark_bar(
    cornerRadiusTopLeft=4, cornerRadiusTopRight=4
).encode(
    x=alt.X("Parent_Education:N", title=None, sort=edu_order, axis=alt.Axis(labelAngle=-45)),
    y=alt.Y("GPA:Q", title="12th Grade GPA", scale=alt.Scale(domain=[2.5, 3.5])),
    color=alt.Color("Parent_Education:N",
                    scale=alt.Scale(domain=edu_order, scheme="viridis"),
                    legend=None),
    tooltip=["Parent_Education:N", alt.Tooltip("GPA:Q", format=".2f"),
             alt.Tooltip("Count:Q", format=",d", title="Students")]
).transform_filter(edu_select).properties(
    title={"text": "Final GPA", "color": "#FFFFFF", "fontSize": 14},
    width=250, height=300
)

viz4 = alt.hconcat(left_chart, right_chart).resolve_scale(color="independent")
save_chart(viz4, "combined_gender_stem.json")


print("\n" + "="*60)
print("VIZ 5: The Gender Paradox - Girls Expect STEM But Choose Differently")
print("="*60)

hsls_stem = hsls_df[(hsls_df["X1SEX"].isin([1, 2])) &
                     (hsls_df["X1STU30OCC_STEM1"].notna()) &
                     (hsls_df["X4RFDGMJSTEM"].notna())].copy()
hsls_stem["Gender"] = hsls_stem["X1SEX"].map({1: "Male", 2: "Female"})
hsls_stem["STEM_Expect"] = hsls_stem["X1STU30OCC_STEM1"] == 1
hsls_stem["STEM_Major"] = hsls_stem["X4RFDGMJSTEM"] == 1

expect_rates = hsls_stem.groupby("Gender")["STEM_Expect"].mean() * 100
major_rates = hsls_stem.groupby("Gender")["STEM_Major"].mean() * 100

driver_data = pd.DataFrame([
    {"Metric": "9th Grade STEM Expectation", "Gender": "Female", "Percentage": expect_rates["Female"]},
    {"Metric": "9th Grade STEM Expectation", "Gender": "Male", "Percentage": expect_rates["Male"]},
    {"Metric": "College STEM Major", "Gender": "Female", "Percentage": major_rates["Female"]},
    {"Metric": "College STEM Major", "Gender": "Male", "Percentage": major_rates["Male"]}
])

stem_expecters = hsls_stem[hsls_stem["STEM_Expect"] == True]
conversion_rates = stem_expecters.groupby("Gender")["STEM_Major"].mean() * 100
driven_data = pd.DataFrame([
    {"Gender": "Female", "Conversion_Rate": conversion_rates.get("Female", 0)},
    {"Gender": "Male", "Conversion_Rate": conversion_rates.get("Male", 0)}
])

metric_select = alt.selection_point(fields=["Metric"], name="metric_select")

left_chart = alt.Chart(driver_data).mark_bar(
    cornerRadiusTopLeft=4, cornerRadiusTopRight=4, cursor="pointer"
).encode(
    x=alt.X("Metric:N", title=None, axis=alt.Axis(labelAngle=-20)),
    y=alt.Y("Percentage:Q", title="Percentage (%)", scale=alt.Scale(domain=[0, 45])),
    color=alt.Color("Gender:N",
                    scale=alt.Scale(domain=["Female", "Male"], range=["#E91E63", "#1976D2"]),
                    legend=alt.Legend(title="Gender", orient="top")),
    xOffset="Gender:N",
    opacity=alt.condition(metric_select, alt.value(1), alt.value(0.3)),
    tooltip=["Metric:N", "Gender:N", alt.Tooltip("Percentage:Q", format=".1f")]
).add_params(metric_select).properties(
    name="view_1",
    title={"text": "Click Metric", "color": "#FFFFFF", "fontSize": 14},
    width=350, height=300
)

right_chart = alt.Chart(driven_data).mark_bar(
    cornerRadiusTopLeft=4, cornerRadiusTopRight=4
).encode(
    x=alt.X("Gender:N", title=None),
    y=alt.Y("Conversion_Rate:Q", title="STEM Conversion Rate (%)", scale=alt.Scale(domain=[0, 50])),
    color=alt.Color("Gender:N",
                    scale=alt.Scale(domain=["Female", "Male"], range=["#E91E63", "#1976D2"]),
                    legend=None),
    tooltip=["Gender:N", alt.Tooltip("Conversion_Rate:Q", format=".1f", title="Conversion Rate")]
).properties(
    title={"text": "Who Follows Through?", "color": "#FFFFFF", "fontSize": 14},
    width=200, height=300
)

viz5 = alt.hconcat(left_chart, right_chart).resolve_scale(color="independent")
save_chart(viz5, "hsls_math_identity_race.json")


print("\n" + "="*60)
print("VIZ 6: Socioeconomic Status Predicts STEM Major Selection")
print("="*60)

hsls_ses = hsls_df[(hsls_df["X1SESQ5"].notna()) &
                    (hsls_df["X4RFDGMJSTEM"].notna())].copy()
hsls_ses = hsls_ses[hsls_ses["X1SESQ5"] > 0]

ses_labels = {1: "Lowest 20%", 2: "Second 20%", 3: "Middle 20%", 4: "Fourth 20%", 5: "Highest 20%"}
hsls_ses["Income_Group"] = hsls_ses["X1SESQ5"].map(ses_labels)
hsls_ses["STEM_Major"] = hsls_ses["X4RFDGMJSTEM"] == 1

driver_data = hsls_ses.groupby("Income_Group").agg(
    STEM_Rate=("STEM_Major", "mean"),
    Count=("STEM_Major", "count")
).reset_index()
driver_data["STEM_Rate"] = driver_data["STEM_Rate"] * 100

stem_counts = hsls_ses.groupby(["Income_Group", "STEM_Major"]).size().unstack(fill_value=0)
stem_props = stem_counts.div(stem_counts.sum(axis=1), axis=0).reset_index()
driven_data = pd.melt(stem_props, id_vars=["Income_Group"], var_name="STEM_Major", value_name="Proportion")
driven_data["Proportion"] = driven_data["Proportion"] * 100
driven_data["Major_Type"] = driven_data["STEM_Major"].map({True: "STEM", False: "Non-STEM"})

ses_order = ["Lowest 20%", "Second 20%", "Middle 20%", "Fourth 20%", "Highest 20%"]
ses_select = alt.selection_point(fields=["Income_Group"], name="ses_select")

left_chart = alt.Chart(driver_data).mark_bar(
    cornerRadiusTopLeft=4, cornerRadiusTopRight=4, cursor="pointer"
).encode(
    x=alt.X("Income_Group:N", title="Family Income Quintile", sort=ses_order, axis=alt.Axis(labelAngle=-45)),
    y=alt.Y("STEM_Rate:Q", title="STEM Major Rate (%)", scale=alt.Scale(domain=[0, 35])),
    color=alt.Color("Income_Group:N",
                    scale=alt.Scale(domain=ses_order, scheme="blues"),
                    legend=None),
    opacity=alt.condition(ses_select, alt.value(1), alt.value(0.3)),
    tooltip=["Income_Group:N", alt.Tooltip("STEM_Rate:Q", format=".1f"),
             alt.Tooltip("Count:Q", format=",d", title="Students")]
).add_params(ses_select).properties(
    name="view_1",
    title={"text": "Click Income Level", "color": "#FFFFFF", "fontSize": 14},
    width=350, height=300
)

right_chart = alt.Chart(driven_data).mark_bar().encode(
    y=alt.Y("Income_Group:N", title=None, sort=ses_order),
    x=alt.X("Proportion:Q", title="Percentage (%)", scale=alt.Scale(domain=[0, 100]), stack="normalize"),
    color=alt.Color("Major_Type:N",
                    scale=alt.Scale(domain=["STEM", "Non-STEM"], range=["#4caf50", "#9e9e9e"]),
                    legend=alt.Legend(title="Major Type", orient="top")),
    order=alt.Order("Major_Type:N", sort="descending"),
    tooltip=["Income_Group:N", "Major_Type:N", alt.Tooltip("Proportion:Q", format=".1f")]
).transform_filter(ses_select).properties(
    title={"text": "STEM vs Non-STEM", "color": "#FFFFFF", "fontSize": 14},
    width=250, height=300
)

viz6 = alt.hconcat(left_chart, right_chart).resolve_scale(color="independent")
save_chart(viz6, "hsls_gpa_ses_trajectory.json")


print("\n" + "="*60)
print("VIZ 7: The SES-Achievement Gap Across Datasets")
print("="*60)

pisa_ses = pisa_df[(pisa_df["ESCS"].notna()) & (pisa_df["PV1MATH"].notna())].copy()
pisa_ses["SES_Quintile"] = pd.qcut(pisa_ses["ESCS"], 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
pisa_agg = pisa_ses.groupby("SES_Quintile").agg(Math_Score=("PV1MATH", "mean")).reset_index()
pisa_agg["Source"] = "PISA (International)"

hsls_ses_data = hsls_df[(hsls_df["X1SESQ5"].notna()) & (hsls_df["X1TXMTSCOR"].notna())].copy()
hsls_ses_data = hsls_ses_data[hsls_ses_data["X1SESQ5"] > 0]
ses_map = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5"}
hsls_ses_data["SES_Quintile"] = hsls_ses_data["X1SESQ5"].map(ses_map)
hsls_agg = hsls_ses_data.groupby("SES_Quintile").agg(Math_Score=("X1TXMTSCOR", "mean")).reset_index()
hsls_agg["Source"] = "HSLS (US)"

quintile_order = ["Q1", "Q2", "Q3", "Q4", "Q5"]
ses_highlight = alt.selection_point(fields=["SES_Quintile"], name="ses_highlight")

left_chart = alt.Chart(pisa_agg).mark_line(
    point={"filled": True, "size": 100}, strokeWidth=4, cursor="pointer"
).encode(
    x=alt.X("SES_Quintile:O", title="SES Quintile", sort=quintile_order),
    y=alt.Y("Math_Score:Q", title="Average Math Score", scale=alt.Scale(domain=[400, 550])),
    color=alt.value("#4c8dff"),
    opacity=alt.condition(ses_highlight, alt.value(1), alt.value(0.3)),
    tooltip=["SES_Quintile:N", alt.Tooltip("Math_Score:Q", format=".1f")]
).add_params(ses_highlight).properties(
    name="view_1",
    title={"text": "PISA (International)", "color": "#FFFFFF", "fontSize": 14},
    width=300, height=300
)

right_chart = alt.Chart(hsls_agg).mark_line(
    point={"filled": True, "size": 100}, strokeWidth=4
).encode(
    x=alt.X("SES_Quintile:O", title="SES Quintile", sort=quintile_order),
    y=alt.Y("Math_Score:Q", title="Average Math Score", scale=alt.Scale(domain=[40, 60])),
    color=alt.value("#a855f7"),
    opacity=alt.condition(ses_highlight, alt.value(1), alt.value(0.3)),
    tooltip=["SES_Quintile:N", alt.Tooltip("Math_Score:Q", format=".1f")]
).properties(
    title={"text": "HSLS (US)", "color": "#FFFFFF", "fontSize": 14},
    width=300, height=300
)

viz7 = alt.hconcat(left_chart, right_chart).resolve_scale(color="independent")
save_chart(viz7, "combined_efficacy_comparison.json")


print("\n" + "="*60)
print("VIZ 8: Math Confidence Predicts Performance")
print("="*60)

pisa_eff = pisa_df[(pisa_df["MATHEFF"].notna()) & (pisa_df["PV1MATH"].notna())].copy()
pisa_eff["Efficacy_Level"] = pd.qcut(pisa_eff["MATHEFF"], 3, labels=["Low", "Medium", "High"])
pisa_eff_agg = pisa_eff.groupby("Efficacy_Level").agg(Math_Score=("PV1MATH", "mean")).reset_index()
pisa_eff_agg["Source"] = "PISA"

hsls_eff = hsls_df[(hsls_df["X1MTHEFF"].notna()) & (hsls_df["X1TXMTSCOR"].notna())].copy()
hsls_eff["Efficacy_Level"] = pd.qcut(hsls_eff["X1MTHEFF"], 3, labels=["Low", "Medium", "High"])
hsls_eff_agg = hsls_eff.groupby("Efficacy_Level").agg(Math_Score=("X1TXMTSCOR", "mean")).reset_index()
hsls_eff_agg["Source"] = "HSLS"

eff_order = ["Low", "Medium", "High"]
eff_highlight = alt.selection_point(fields=["Efficacy_Level"], name="eff_highlight")

left_chart = alt.Chart(pisa_eff_agg).mark_bar(
    cornerRadiusTopLeft=4, cornerRadiusTopRight=4, cursor="pointer"
).encode(
    x=alt.X("Efficacy_Level:N", title="Math Confidence", sort=eff_order),
    y=alt.Y("Math_Score:Q", title="Average Math Score", scale=alt.Scale(domain=[400, 540])),
    color=alt.Color("Efficacy_Level:N",
                    scale=alt.Scale(domain=eff_order, scheme="greens"),
                    legend=None),
    opacity=alt.condition(eff_highlight, alt.value(1), alt.value(0.3)),
    tooltip=["Efficacy_Level:N", alt.Tooltip("Math_Score:Q", format=".1f")]
).add_params(eff_highlight).properties(
    name="view_1",
    title={"text": "PISA (International)", "color": "#FFFFFF", "fontSize": 14},
    width=250, height=300
)

right_chart = alt.Chart(hsls_eff_agg).mark_bar(
    cornerRadiusTopLeft=4, cornerRadiusTopRight=4
).encode(
    x=alt.X("Efficacy_Level:N", title="Math Confidence", sort=eff_order),
    y=alt.Y("Math_Score:Q", title="Average Math Score", scale=alt.Scale(domain=[40, 58])),
    color=alt.Color("Efficacy_Level:N",
                    scale=alt.Scale(domain=eff_order, scheme="greens"),
                    legend=None),
    opacity=alt.condition(eff_highlight, alt.value(1), alt.value(0.3)),
    tooltip=["Efficacy_Level:N", alt.Tooltip("Math_Score:Q", format=".1f")]
).properties(
    title={"text": "HSLS (US)", "color": "#FFFFFF", "fontSize": 14},
    width=250, height=300
)

viz8 = alt.hconcat(left_chart, right_chart).resolve_scale(color="independent")
save_chart(viz8, "combined_ses_achievement.json")


print("\n" + "="*60)
print("VIZ 9: Parent Education Premium Across Datasets (Dual Y-Axes)")
print("="*60)

hsls_edu_map = {1: "Less than HS", 2: "High School", 3: "Some College",
                4: "Some College", 5: "Bachelor's", 6: "Graduate+", 7: "Graduate+"}
pisa_edu_map = {1: "Less than HS", 2: "Less than HS", 3: "High School",
                4: "Some College", 5: "Some College", 6: "Bachelor's",
                7: "Graduate+", 8: "Graduate+"}

hsls_edu = hsls_df[(hsls_df["X1PAR1EDU"].notna()) & (hsls_df["X1TXMTSCOR"].notna())].copy()
hsls_edu = hsls_edu[hsls_edu["X1PAR1EDU"] > 0]
hsls_edu["Parent_Education"] = hsls_edu["X1PAR1EDU"].map(hsls_edu_map)
hsls_agg = hsls_edu.groupby("Parent_Education").agg(Math_Score=("X1TXMTSCOR", "mean")).reset_index()
hsls_agg["Source"] = "HSLS (US 2009)"

pisa_edu = pisa_df[(pisa_df["HISCED"].notna()) & (pisa_df["PV1MATH"].notna())].copy()
pisa_edu = pisa_edu[pisa_edu["HISCED"] > 0]
pisa_edu["Parent_Education"] = pisa_edu["HISCED"].map(pisa_edu_map)

pisa_us = pisa_edu[pisa_edu["CNT"] == "USA"]
pisa_us_agg = pisa_us.groupby("Parent_Education").agg(Math_Score=("PV1MATH", "mean")).reset_index()
pisa_us_agg["Source"] = "PISA US (2022)"

pisa_intl = pisa_edu[pisa_edu["CNT"] != "USA"]
pisa_intl_agg = pisa_intl.groupby("Parent_Education").agg(Math_Score=("PV1MATH", "mean")).reset_index()
pisa_intl_agg["Source"] = "PISA Intl (2022)"

combined = pd.concat([hsls_agg, pisa_us_agg, pisa_intl_agg])

baseline = combined[combined["Parent_Education"] == "Less than HS"].set_index("Source")["Math_Score"].to_dict()
combined["Premium"] = combined.apply(lambda r: r["Math_Score"] - baseline.get(r["Source"], r["Math_Score"]), axis=1)

edu_order = ["Less than HS", "High School", "Some College", "Bachelor's", "Graduate+"]
source_order = ["HSLS (US 2009)", "PISA US (2022)", "PISA Intl (2022)"]
source_colors = ["#E69F00", "#56B4E9", "#009E73"]

edu_select = alt.selection_point(fields=["Parent_Education"], name="edu_select")

left_chart = alt.Chart(combined).mark_line(
    point={"filled": True, "size": 80}, strokeWidth=3, cursor="pointer"
).encode(
    x=alt.X("Parent_Education:O", title="Parent Education", sort=edu_order, axis=alt.Axis(labelAngle=-45)),
    y=alt.Y("Math_Score:Q", title="Math Score (Raw Units)"),
    color=alt.Color("Source:N",
                    scale=alt.Scale(domain=source_order, range=source_colors),
                    legend=alt.Legend(title="Data Source", orient="top")),
    opacity=alt.condition(edu_select, alt.value(1), alt.value(0.3)),
    tooltip=["Parent_Education:N", "Source:N", alt.Tooltip("Math_Score:Q", format=".1f")]
).add_params(edu_select).properties(
    name="view_1",
    title={"text": "Click Education Level", "color": "#FFFFFF", "fontSize": 14},
    width=450, height=350
)

right_chart = alt.Chart(combined).mark_bar(
    cornerRadiusTopLeft=4, cornerRadiusTopRight=4
).encode(
    x=alt.X("Source:N", title=None, sort=source_order, axis=alt.Axis(labelAngle=-30)),
    y=alt.Y("Premium:Q", title="Score Premium vs Less than HS"),
    color=alt.Color("Source:N",
                    scale=alt.Scale(domain=source_order, range=source_colors),
                    legend=None),
    tooltip=["Parent_Education:N", "Source:N", alt.Tooltip("Premium:Q", format=".1f", title="Premium")]
).transform_filter(edu_select).properties(
    title={"text": "Education Premium", "color": "#FFFFFF", "fontSize": 14},
    width=250, height=350
)

viz9 = alt.hconcat(left_chart, right_chart).resolve_scale(color="independent")
save_chart(viz9, "combined_parent_education.json")


print("\n" + "="*60)
print("VERIFICATION")
print("="*60)
import os
json_files = [
    "pisa_gender_efficacy_dumbbell.json",
    "pisa_anxiety_performance_heatmap.json",
    "combined_immigration.json",
    "combined_gender_stem.json",
    "hsls_math_identity_race.json",
    "hsls_gpa_ses_trajectory.json",
    "combined_efficacy_comparison.json",
    "combined_ses_achievement.json",
    "combined_parent_education.json"
]

print("\nGenerated JSON files:")
for f in json_files:
    path = OUTPUT_DIR / f
    if path.exists():
        size = os.path.getsize(path)
        print(f"  {f}: {size/1024:.1f} KB")
    else:
        print(f"  {f}: NOT FOUND")

print("\nAll 9 visualizations generated successfully!")
