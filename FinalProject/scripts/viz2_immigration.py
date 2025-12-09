import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory = False)

v2_immig_map = {1: "Native", 2: "Second-gen", 3: "First-gen"}
v2_immig_order = ["Native", "Second-gen", "First-gen"]

v2_data = pisa_df[(pisa_df["IMMIG"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2])) &
                   (pisa_df["BELONG"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["PV1READ"].notna()) &
                   (pisa_df["PV1SCIE"].notna())].copy()
v2_data = v2_data[(v2_data["IMMIG"] > 0) & (v2_data["IMMIG"] <= 3)]

v2_data["Immigration_Status"] = v2_data["IMMIG"].map(v2_immig_map)
v2_data["Gender"] = v2_data["ST004D01T"].map({1: "Female", 2: "Male"})

v2_immig_gender_belong = v2_data.groupby(["Immigration_Status", "Gender"]).agg(
    Avg_Belonging = ("BELONG", "mean"),
    Count = ("BELONG", "count")
).reset_index()

v2_immig_select = alt.selection_point(fields = ["Immigration_Status"], name = "immig_select")

v2_left_chart = alt.Chart(v2_immig_gender_belong).mark_bar(
    cornerRadius = 4, cursor = "pointer"
).encode(
    x = alt.X("Immigration_Status:N", title = "Immigration Status", sort = v2_immig_order,
             axis = alt.Axis(labelAngle = 0, labelFontSize = 11)),
    y = alt.Y("Avg_Belonging:Q", title = "Average School Belonging Score"),
    xOffset = alt.XOffset("Gender:N", sort = ["Female", "Male"]),
    color = alt.Color("Gender:N", title = "Gender",
                     scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]),
                     legend = alt.Legend(orient = "top")),
    opacity = alt.condition(v2_immig_select, alt.value(1), alt.value(0.4)),
    tooltip = ["Immigration_Status:N", "Gender:N",
              alt.Tooltip("Avg_Belonging:Q", format = ".2f", title = "Avg Belonging"),
              alt.Tooltip("Count:Q", format = ",d", title = "Students")]
).add_params(v2_immig_select).properties(
    name = "view_1",
    title = {"text": "School Belonging by Immigration Status",
            "subtitle": "Click to see performance by domain",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 380, height = 400
)

v2_immig_performance = v2_data.groupby("Immigration_Status").agg(
    Math = ("PV1MATH", "mean"),
    Reading = ("PV1READ", "mean"),
    Science = ("PV1SCIE", "mean"),
    Count = ("PV1MATH", "count")
).reset_index()

v2_immig_perf_long = v2_immig_performance.melt(
    id_vars = ["Immigration_Status", "Count"],
    value_vars = ["Math", "Reading", "Science"],
    var_name = "Domain",
    value_name = "Avg_Score"
)

v2_right_chart = alt.Chart(v2_immig_perf_long).mark_bar(cornerRadius = 4).encode(
    x = alt.X("Domain:N", title = None, sort = ["Math", "Reading", "Science"],
             axis = alt.Axis(labelAngle = 0, labelFontSize = 11)),
    y = alt.Y("Avg_Score:Q", title = "Average Score", scale = alt.Scale(domain = [400, 520])),
    xOffset = alt.XOffset("Immigration_Status:N", sort = v2_immig_order),
    color = alt.Color("Immigration_Status:N", title = "Immigration Status",
                     scale = alt.Scale(domain = v2_immig_order,
                                      range = ["#4CAF50", "#FF9800", "#9C27B0"]),
                     legend = alt.Legend(orient = "top")),
    opacity = alt.condition(v2_immig_select, alt.value(1), alt.value(0.3)),
    tooltip = [alt.Tooltip("Immigration_Status:N", title = "Status"),
              alt.Tooltip("Domain:N", title = "Domain"),
              alt.Tooltip("Avg_Score:Q", format = ".1f", title = "Avg Score")]
).properties(
    title = {"text": "Performance by Domain & Immigration Status",
            "subtitle": "Filtered by immigration status selection",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 400, height = 400
)

viz2 = alt.hconcat(v2_left_chart, v2_right_chart).resolve_scale(color = "independent")
save_chart(viz2, "combined_immigration.json")
