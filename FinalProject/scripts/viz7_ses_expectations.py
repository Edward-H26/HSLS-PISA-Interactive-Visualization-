import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart, OECD_COUNTRIES

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory = False)
hsls_df = pd.read_csv(DATA_DIR / "hsls_subset.csv", low_memory = False)

v7_pisa = pisa_df[(pisa_df["ESCS"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["CNT"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2]))].copy()

v7_pv_cols = [f"PV{i}MATH" for i in range(1, 11)]
v7_available_pv = [col for col in v7_pv_cols if col in v7_pisa.columns]
v7_pisa["Math_Score"] = v7_pisa[v7_available_pv].mean(axis = 1)
v7_pisa["Gender"] = v7_pisa["ST004D01T"].map({1: "Female", 2: "Male"})

v7_country_gender_agg = v7_pisa.groupby(["CNT", "Gender"]).agg(
    Mean_ESCS = ("ESCS", "mean"),
    Mean_Math = ("Math_Score", "mean"),
    n = ("CNT", "size")
).reset_index()

v7_country_gender_agg["OECD_Status"] = v7_country_gender_agg["CNT"].apply(
    lambda x: "OECD" if x in OECD_COUNTRIES else "Non-OECD"
)
v7_country_gender_agg["Gender_OECD"] = v7_country_gender_agg["Gender"] + " " + v7_country_gender_agg["OECD_Status"]

v7_hsls = hsls_df[(hsls_df["X1TXMQUINT"].notna()) &
                   (hsls_df["X1STUEDEXPCT"].notna()) &
                   (hsls_df["X1SESQ5"].notna()) &
                   (hsls_df["X1SEX"].isin([1, 2]))].copy()
v7_hsls = v7_hsls[(v7_hsls["X1TXMQUINT"] > 0) &
                   (v7_hsls["X1STUEDEXPCT"] > 0) &
                   (v7_hsls["X1SESQ5"] > 0)]

v7_hsls["Gender"] = v7_hsls["X1SEX"].map({1: "Male", 2: "Female"})
v7_hsls["Math_Quintile"] = v7_hsls["X1TXMQUINT"].map({
    1: "Q1 (Lowest)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (Highest)"
})
v7_hsls["SES_Quintile"] = v7_hsls["X1SESQ5"].map({
    1: "Q1 (Lowest)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (Highest)"
})
v7_hsls["Ed_Expect_Num"] = v7_hsls["X1STUEDEXPCT"]

v7_hsls_agg = v7_hsls.groupby(["Gender", "Math_Quintile", "SES_Quintile"]).agg(
    Mean_Ed_Expect = ("Ed_Expect_Num", "mean"),
    n = ("Ed_Expect_Num", "size")
).reset_index()

v7_brush_select = alt.selection_interval(name = "brush_select")

v7_quintile_order = ["Q1 (Lowest)", "Q2", "Q3", "Q4", "Q5 (Highest)"]
v7_ses_colors = ["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"]

v7_gender_oecd_domain = ["Female OECD", "Female Non-OECD", "Male OECD", "Male Non-OECD"]
v7_gender_oecd_colors = ["#E91E63", "#F48FB1", "#1976D2", "#64B5F6"]

v7_left_chart = alt.Chart(v7_country_gender_agg).mark_circle(size = 80, cursor = "crosshair").encode(
    x = alt.X("Mean_ESCS:Q", title = "Mean SES (ESCS)",
              scale = alt.Scale(domain = [-2.5, 1.0])),
    y = alt.Y("Mean_Math:Q", title = "Mean Math Score (PV1-10)",
              scale = alt.Scale(domain = [300, 600])),
    color = alt.Color("Gender_OECD:N",
                   scale = alt.Scale(domain = v7_gender_oecd_domain, range = v7_gender_oecd_colors),
                   legend = alt.Legend(title = "Gender & OECD", orient = "top")),
    opacity = alt.condition(v7_brush_select, alt.value(1), alt.value(0.3)),
    tooltip = [
        alt.Tooltip("CNT:N", title = "Country"),
        alt.Tooltip("Gender:N"),
        alt.Tooltip("OECD_Status:N", title = "OECD Status"),
        alt.Tooltip("Mean_ESCS:Q", title = "Mean SES", format = ".2f"),
        alt.Tooltip("Mean_Math:Q", title = "Mean Math", format = ".0f"),
        alt.Tooltip("n:Q", title = "Students", format = ",d")
    ]
).add_params(v7_brush_select).properties(
    name = "view_1",
    title = {"text": "PISA: Country-Level SES vs Math",
           "subtitle": "Drag to select and highlight countries",
           "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 320, height = 300
)

v7_right_chart = alt.Chart(v7_hsls_agg).mark_bar(clip = True).encode(
    x = alt.X("Math_Quintile:N", title = "Math Quintile", sort = v7_quintile_order,
            axis = alt.Axis(labelAngle = -45),
            scale = alt.Scale(paddingOuter = 0.2)),
    y = alt.Y("Mean_Ed_Expect:Q", title = "Mean Ed Expectation Level",
            scale = alt.Scale(domain = [5.5, 9.0], zero = False)),
    color = alt.Color("SES_Quintile:N", title = "SES Quintile",
                   scale = alt.Scale(domain = v7_quintile_order, range = v7_ses_colors),
                   legend = alt.Legend(orient = "top")),
    xOffset = alt.XOffset("SES_Quintile:N", sort = v7_quintile_order,
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

viz7 = alt.hconcat(v7_left_chart, v7_right_chart).resolve_scale(color = "independent")
save_chart(viz7, "combined_efficacy_comparison.json")
