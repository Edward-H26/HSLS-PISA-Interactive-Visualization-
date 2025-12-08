import pandas as pd
import altair as alt
from pathlib import Path
import json
import numpy as np

# Enable large datasets just in case, though we aggregate
alt.data_transformers.disable_max_rows()

# Paths
DATA_DIR = Path("../data")
OUTPUT_DIR = Path("../assets/json")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load Data
print("Loading data...")
hsls_df = pd.read_csv(DATA_DIR / "hsls_subset.csv", low_memory=False)

# Theme Config (Dark Mode)
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
    "title": {"color": "#FFFFFF", "subtitleColor": "#B0B0B0"}
}

def save_chart(chart, filename):
    spec = json.loads(chart.to_json())
    spec["config"] = DARK_CONFIG
    output_path = OUTPUT_DIR / filename
    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"Saved chart to {output_path}")

# --- Preprocessing (Copied from generate_viz_v3.py) ---
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

# Orders
parent_edu_order_v5 = ["Less than HS", "HS Diploma/GED", "Associate's", "Bachelor's", "Master's", "Ph.D/Prof. Degree"]
expect_order = ["HS or Less", "Associate's", "Bachelor's", "Graduate/Prof"]
locale_order_v5 = ["City", "Suburb", "Town", "Rural"]

# --- Redesign Construction ---

# 1. Aggregate for Heatmap (Income vs Parent Edu -> STEM Rate)
heatmap_data = hsls_v5.groupby(["parent_education", "family_income_numeric"]).agg(
    stem_rate=("expected_stem_2009", "mean"),
    student_count=("expected_stem_2009", "count")
).reset_index()

# 2. Aggregate for Bar Chart (Parent Edu, Income, Locale, Gender -> STEM Rate)
# We need to keep enough granularity to filter by the brush
bar_data = hsls_v5.groupby(["parent_education", "family_income_numeric", "school_locale", "gender"]).agg(
    stem_rate=("expected_stem_2009", "mean"),
    student_count=("expected_stem_2009", "count")
).reset_index()

# Selection
brush = alt.selection_interval(name="brush")

# Chart 1: Heatmap (Overview)
heatmap = alt.Chart(heatmap_data).mark_rect(stroke="black", strokeWidth=0.5).encode(
    x=alt.X("family_income_numeric:O", title="Family Income ($)",
            axis=alt.Axis(labelAngle=-45, format="$,.0f")),
    y=alt.Y("parent_education:N", title="Parent Education", sort=parent_edu_order_v5),
    color=alt.Color("stem_rate:Q", title="STEM Expectation Rate",
                   scale=alt.Scale(scheme="viridis", domain=[0, 0.4])),
    tooltip=[
        alt.Tooltip("parent_education:N", title="Education"),
        alt.Tooltip("family_income_numeric:Q", title="Income", format="$,.0f"),
        alt.Tooltip("stem_rate:Q", title="STEM Rate", format=".1%"),
        alt.Tooltip("student_count:Q", title="Students", format=",d")
    ],
    opacity=alt.condition(brush, alt.value(1), alt.value(0.3))
).add_params(brush).properties(
    title={"text": "Impact of SES on STEM Expectations", "subtitle": "Drag to select a demographic range"},
    width=400,
    height=350
)

# Chart 2: Detailed Bar Chart (Breakdown by Locale & Gender)
# We show the STEM rate for the selected population, broken down by Locale and Gender
detail_chart = alt.Chart(bar_data).transform_filter(brush).mark_bar().encode(
    x=alt.X("school_locale:N", title="School Locale", sort=locale_order_v5),
    y=alt.Y("mean(stem_rate):Q", title="Avg STEM Expectation Rate", scale=alt.Scale(domain=[0, 0.5])),
    color=alt.Color("gender:N", title="Gender", scale=alt.Scale(domain=["Male", "Female"], range=["#1976D2", "#E91E63"])),
    xOffset=alt.XOffset("gender:N"),
    tooltip=[
        alt.Tooltip("school_locale:N"),
        alt.Tooltip("gender:N"),
        alt.Tooltip("mean(stem_rate):Q", title="STEM Rate", format=".1%")
    ]
).properties(
    title={"text": "STEM Expectations by Locale & Gender", "subtitle": "For selected SES range"},
    width=350,
    height=350
)

# Combine
viz5_redesign = alt.hconcat(heatmap, detail_chart).resolve_scale(color="independent")

# Save
save_chart(viz5_redesign, "hsls_math_identity_race.json")
