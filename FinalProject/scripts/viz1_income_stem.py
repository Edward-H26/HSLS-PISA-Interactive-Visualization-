import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart

hsls_df = pd.read_csv(DATA_DIR / "hsls_subset.csv", low_memory = False)

v1_parent_edu_map = {
    1: "Less than HS", 1.0: "Less than HS",
    2: "HS Diploma/GED", 2.0: "HS Diploma/GED",
    3: "Associate's", 3.0: "Associate's",
    4: "Bachelor's", 4.0: "Bachelor's",
    5: "Master's", 5.0: "Master's",
    7: "Ph.D/Prof. Degree", 7.0: "Ph.D/Prof. Degree"
}
v1_student_expect_map = {
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
v1_income_map = {
    1: 7500, 1.0: 7500, 2: 25000, 2.0: 25000, 3: 45000, 3.0: 45000,
    4: 65000, 4.0: 65000, 5: 85000, 5.0: 85000, 6: 105000, 6.0: 105000,
    7: 125000, 7.0: 125000, 8: 145000, 8.0: 145000, 9: 165000, 9.0: 165000,
    10: 185000, 10.0: 185000, 11: 205000, 11.0: 205000, 12: 225000, 12.0: 225000,
    13: 250000, 13.0: 250000
}
v1_locale_map = {1: "City", 1.0: "City", 2: "Suburb", 2.0: "Suburb", 3: "Town", 3.0: "Town", 4: "Rural", 4.0: "Rural"}
v1_stem_map = {0: 0, 0.0: 0, 1: 1, 1.0: 1, 2: 1, 2.0: 1, 3: 1, 3.0: 1, 4: 1, 4.0: 1, 5: 1, 5.0: 1, 6: 1, 6.0: 1}

v1_data = hsls_df[(hsls_df["X1PAR1EDU"].notna()) &
                   (hsls_df["X1FAMINCOME"].notna()) &
                   (hsls_df["X1STUEDEXPCT"].notna()) &
                   (hsls_df["X1SEX"].isin([1, 2])) &
                   (hsls_df["X1LOCALE"].notna()) &
                   (hsls_df["X1STU30OCC_STEM1"].notna())].copy()

v1_data["parent_education"] = v1_data["X1PAR1EDU"].map(v1_parent_edu_map).fillna("Unknown")
v1_data["student_ed_expect"] = v1_data["X1STUEDEXPCT"].map(v1_student_expect_map).fillna("Unknown")
v1_data["family_income_numeric"] = v1_data["X1FAMINCOME"].map(v1_income_map)
v1_data["gender"] = v1_data["X1SEX"].map({1: "Male", 1.0: "Male", 2: "Female", 2.0: "Female"})
v1_data["school_locale"] = v1_data["X1LOCALE"].map(v1_locale_map).fillna("Unknown")
v1_data["expected_stem_2009"] = v1_data["X1STU30OCC_STEM1"].map(v1_stem_map)

v1_parent_edu_order = ["Less than HS", "HS Diploma/GED", "Associate's", "Bachelor's", "Master's", "Ph.D/Prof. Degree"]
v1_expect_order = ["HS or Less", "Associate's", "Bachelor's", "Graduate/Prof"]
v1_locale_order = ["City", "Suburb", "Town", "Rural"]

v1_income_df = v1_data[
    (v1_data["parent_education"].isin(v1_parent_edu_order)) &
    (v1_data["student_ed_expect"].isin(v1_expect_order)) &
    (v1_data["family_income_numeric"].notna())
].groupby(["parent_education", "student_ed_expect"]).agg(
    avg_income = ("family_income_numeric", "mean"),
    student_count = ("family_income_numeric", "count")
).reset_index()

v1_stem_df = v1_data[
    (v1_data["school_locale"].isin(v1_locale_order)) &
    (v1_data["gender"].isin(["Male", "Female"])) &
    (v1_data["expected_stem_2009"].notna())
].groupby(["school_locale", "gender", "parent_education"]).agg(
    stem_rate = ("expected_stem_2009", "mean"),
    student_count = ("expected_stem_2009", "count")
).reset_index()

v1_expect_colors = ["#E57373", "#FFB74D", "#81C784", "#64B5F6"]
v1_gender_colors = ["#1976D2", "#E91E63"]

v1_edu_selection = alt.selection_point(fields = ["parent_education"], name = "edu_select")

v1_left_chart = alt.Chart(v1_income_df).mark_bar(
    cursor = "pointer", cornerRadiusTopRight = 3, cornerRadiusTopLeft = 3,
    stroke = "#0f172a", strokeWidth = 0.8
).encode(
    x = alt.X("parent_education:N", title = "Parent Education Level", sort = v1_parent_edu_order,
             axis = alt.Axis(labelAngle = -45, labelFontSize = 10, labelPadding = 8, titleFontSize = 14)),
    xOffset = alt.XOffset("student_ed_expect:N", sort = v1_expect_order),
    y = alt.Y("avg_income:Q", title = "Average Family Income ($)",
             axis = alt.Axis(labelFontSize = 12, titleFontSize = 14, grid = True, gridOpacity = 0.3, format = "$,.0f"),
             scale = alt.Scale(domain = [0, 180000])),
    color = alt.Color("student_ed_expect:N", title = "Student Expectations", sort = v1_expect_order,
                     scale = alt.Scale(domain = v1_expect_order, range = v1_expect_colors),
                     legend = alt.Legend(titleFontSize = 11, labelFontSize = 9, orient = "bottom",
                                        direction = "horizontal", symbolSize = 60, padding = 8,
                                        titlePadding = 8, columns = 4, offset = 10, labelLimit = 120)),
    opacity = alt.condition(v1_edu_selection, alt.value(1), alt.value(0.3)),
    tooltip = [alt.Tooltip("parent_education:N", title = "Parent Education"),
              alt.Tooltip("student_ed_expect:N", title = "Student Expectations"),
              alt.Tooltip("avg_income:Q", title = "Avg Family Income", format = "$,.0f"),
              alt.Tooltip("student_count:Q", title = "Students", format = ",d")]
).add_params(v1_edu_selection).properties(
    width = 450, height = 450,
    title = alt.TitleParams(
        text = "Association Between Parental Education and Family Income",
        subtitle = "Stratified by student educational expectations (HSLS:09)",
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

v1_right_chart = alt.Chart(v1_stem_df).transform_filter(v1_edu_selection).mark_bar(
    cornerRadiusTopRight = 4, cornerRadiusBottomRight = 4,
    stroke = "#0f172a", strokeWidth = 0.8
).encode(
    y = alt.Y("school_locale:N", title = "School Location", sort = v1_locale_order,
             axis = alt.Axis(labelFontSize = 13, labelPadding = 8, titleFontSize = 14)),
    yOffset = alt.YOffset("gender:N", sort = ["Male", "Female"]),
    x = alt.X("mean(stem_rate):Q", title = "% Expecting STEM Career at Age 30",
             axis = alt.Axis(format = ".0%", labelFontSize = 12, titleFontSize = 14, grid = True, gridOpacity = 0.3, labelAngle = -45),
             scale = alt.Scale(domain = [0, 0.55])),
    color = alt.Color("gender:N", title = "Gender", sort = ["Male", "Female"],
                     scale = alt.Scale(domain = ["Male", "Female"], range = v1_gender_colors),
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
        text = "STEM Career Expectations at Age 30 by School Locale",
        subtitle = "Gender differences across urban and rural settings",
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

viz1 = alt.hconcat(v1_left_chart, v1_right_chart).resolve_scale(color = "independent")
save_chart(viz1, "hsls_math_identity_race.json")
