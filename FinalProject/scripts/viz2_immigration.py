import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory = False)

v2_hisced_map = {
    0: "None", 1: "Primary", 2: "Lower Secondary",
    3: "Upper Secondary", 4: "Post-Secondary",
    5: "Short-Cycle Tertiary", 6: "Bachelor's",
    7: "Master's", 8: "Doctoral"
}
v2_edu_order = ["None", "Primary", "Lower Secondary", "Upper Secondary",
                "Post-Secondary", "Short-Cycle Tertiary", "Bachelor's", "Master's", "Doctoral"]

v2_immig_map = {1: "Native", 2: "Second-gen", 3: "First-gen"}
v2_immig_order = ["Native", "Second-gen", "First-gen"]
v2_immig_colors = ["#1E88E5", "#FF9800", "#9C27B0"]

v2_ses_order = ["Low SES", "Lower-Mid SES", "Upper-Mid SES", "High SES"]
v2_ses_colors = ["#C8E6C9", "#81C784", "#4CAF50", "#1B5E20"]

v2_data = pisa_df[(pisa_df["HOMEPOS"].notna()) &
                   (pisa_df["ESCS"].notna()) &
                   (pisa_df["HISCED"].notna()) &
                   (pisa_df["IMMIG"].notna()) &
                   (pisa_df["ICTRES"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["PV1READ"].notna()) &
                   (pisa_df["PV1SCIE"].notna())].copy()
v2_data = v2_data[(v2_data["IMMIG"] > 0) & (v2_data["IMMIG"] <= 3)]

v2_data["Immigration_Status"] = v2_data["IMMIG"].map(v2_immig_map)
v2_data["SES_Quartile"] = pd.qcut(v2_data["ESCS"], 4, labels = v2_ses_order)
v2_data["Avg_Performance"] = (v2_data["PV1MATH"] + v2_data["PV1READ"] + v2_data["PV1SCIE"]) / 3
v2_data["Parent_Education"] = v2_data["HISCED"].map(v2_hisced_map).fillna("Unknown")

v2_homepos_bins = pd.cut(v2_data["HOMEPOS"], bins = 10)
v2_data["HOMEPOS_Bin"] = v2_homepos_bins
v2_data["HOMEPOS_Mid"] = v2_homepos_bins.apply(lambda x: x.mid if pd.notna(x) else None)

v2_ses_select = alt.selection_point(fields = ["SES_Quartile"], name = "ses_select")

v2_line_df = v2_data[v2_data["Parent_Education"].isin(v2_edu_order)].groupby(
    ["Parent_Education", "SES_Quartile"], observed = True
).agg(
    Avg_ICTRES = ("ICTRES", "mean"),
    Count = ("ICTRES", "count")
).reset_index()

v2_line_chart = alt.Chart(v2_line_df).mark_line(
    point = alt.OverlayMarkDef(filled = True, size = 80, cursor = "pointer"),
    strokeWidth = 2.5
).encode(
    x = alt.X("Parent_Education:N", title = "Parent Education Level",
             sort = v2_edu_order,
             axis = alt.Axis(labelAngle = -45, labelFontSize = 10, titleFontSize = 12, labelLimit = 100)),
    y = alt.Y("Avg_ICTRES:Q", title = "ICT Resources Index",
             scale = alt.Scale(domain = [-3, 4]),
             axis = alt.Axis(labelFontSize = 11, titleFontSize = 12, grid = True, gridOpacity = 0.3)),
    color = alt.Color("SES_Quartile:N", title = "SES Quartile",
                     scale = alt.Scale(domain = v2_ses_order, range = v2_ses_colors),
                     legend = alt.Legend(orient = "top", titleFontSize = 11, labelFontSize = 10,
                                        direction = "horizontal", columns = 4)),
    opacity = alt.condition(v2_ses_select, alt.value(1), alt.value(0.3)),
    tooltip = [
        alt.Tooltip("Parent_Education:N", title = "Parent Education"),
        alt.Tooltip("SES_Quartile:N", title = "SES Quartile"),
        alt.Tooltip("Avg_ICTRES:Q", title = "ICT Resources", format = ".2f"),
        alt.Tooltip("Count:Q", title = "Sample Size", format = ",d")
    ]
).add_params(v2_ses_select).properties(
    width = 530, height = 480,
    title = alt.TitleParams(
        text = "ICT Resources by Parent Education",
        subtitle = "Click on a line to filter by SES quartile",
        fontSize = 15, subtitleFontSize = 11,
        font = "Roboto, sans-serif", anchor = "middle", fontWeight = 700,
        color = "#FFFFFF", subtitleColor = "#E0E0E0",
        offset = 10, subtitlePadding = 4
    )
)

v2_bubble_df = v2_data.groupby(
    ["HOMEPOS_Mid", "Immigration_Status", "SES_Quartile"], observed = True
).agg(
    Avg_Performance = ("Avg_Performance", "mean"),
    Count = ("Avg_Performance", "count")
).reset_index()

v2_bubble_chart = alt.Chart(v2_bubble_df).transform_filter(
    v2_ses_select
).mark_circle(
    stroke = "#0f172a", strokeWidth = 0.8
).encode(
    x = alt.X("HOMEPOS_Mid:Q", title = "Home Possessions Index",
             axis = alt.Axis(labelFontSize = 11, titleFontSize = 12)),
    y = alt.Y("mean(Avg_Performance):Q", title = "Average Academic Performance",
             scale = alt.Scale(domain = [200, 550]),
             axis = alt.Axis(labelFontSize = 11, titleFontSize = 12, grid = True, gridOpacity = 0.3)),
    color = alt.Color("Immigration_Status:N", title = "Immigration Status",
                     scale = alt.Scale(domain = v2_immig_order, range = v2_immig_colors),
                     legend = alt.Legend(orient = "top", titleFontSize = 11, labelFontSize = 10,
                                        direction = "horizontal", columns = 3)),
    size = alt.Size("sum(Count):Q", title = "Sample Size",
                   scale = alt.Scale(range = [100, 800]), legend = None),
    tooltip = [
        alt.Tooltip("HOMEPOS_Mid:Q", title = "Home Possessions", format = ".2f"),
        alt.Tooltip("Immigration_Status:N", title = "Immigration Status"),
        alt.Tooltip("mean(Avg_Performance):Q", title = "Avg Performance", format = ".1f"),
        alt.Tooltip("sum(Count):Q", title = "Sample Size", format = ",d")
    ]
).properties(
    width = 530, height = 480,
    title = alt.TitleParams(
        text = "Student Performance by Home Possessions",
        subtitle = "Filtered by SES quartile selection",
        fontSize = 15, subtitleFontSize = 11,
        font = "Roboto, sans-serif", anchor = "middle", fontWeight = 700,
        color = "#FFFFFF", subtitleColor = "#E0E0E0",
        offset = 10, subtitlePadding = 4
    )
)

viz2 = alt.hconcat(v2_line_chart, v2_bubble_chart).resolve_scale(color = "independent")
save_chart(viz2, "combined_immigration.json")
