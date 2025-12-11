import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart

hsls_df = pd.read_csv(DATA_DIR / "hsls_subset.csv", low_memory = False)

v4_race_map = {
    1: "Am. Indian/Alaska Native", 1.0: "Am. Indian/Alaska Native",
    2: "Asian", 2.0: "Asian",
    3: "Black/African American", 3.0: "Black/African American",
    4: "Hispanic", 4.0: "Hispanic",
    5: "Hispanic", 5.0: "Hispanic",
    6: "More than one race", 6.0: "More than one race",
    7: "Native Hawaiian/Pacific Islander", 7.0: "Native Hawaiian/Pacific Islander",
    8: "White", 8.0: "White"
}

v4_region_state_map = {
    "Northeast": [9, 23, 25, 33, 44, 50, 34, 36, 42],
    "Midwest": [17, 18, 26, 39, 55, 19, 20, 27, 29, 31, 38, 46],
    "South": [10, 11, 12, 13, 24, 37, 45, 51, 54, 1, 21, 28, 40, 47, 48, 5, 22],
    "West": [4, 8, 16, 30, 32, 35, 49, 56, 2, 6, 15, 41, 53]
}

v4_state_to_region = {}
for region, state_ids in v4_region_state_map.items():
    for state_id in state_ids:
        v4_state_to_region[state_id] = region

v4_race_order = ["White", "Black/African American", "Hispanic", "Asian", "More than one race", "Am. Indian/Alaska Native", "Native Hawaiian/Pacific Islander"]
v4_race_colors = ["#0072B2", "#D55E00", "#E69F00", "#009E73", "#CC79A7", "#F0E442", "#56B4E9"]

v4_data = hsls_df[(hsls_df["X1RACE"].notna()) &
                   (hsls_df["X3TGPA9TH"].notna()) &
                   (hsls_df["X4RFDGMJSTEM"].notna()) &
                   (hsls_df["X1REGION"].notna())].copy()
v4_data = v4_data[(v4_data["X1RACE"] > 0) &
                   (v4_data["X1REGION"] > 0) &
                   (v4_data["X4RFDGMJSTEM"].isin([0, 1]))]

v4_data["race"] = v4_data["X1RACE"].map(v4_race_map).fillna("Unknown")
v4_data["is_stem_major"] = v4_data["X4RFDGMJSTEM"].map({0: 0, 1: 1})

v4_region_mapping = {1: "Northeast", 2: "Midwest", 3: "South", 4: "West"}
v4_data["region"] = v4_data["X1REGION"].map(v4_region_mapping).fillna("Unknown")
v4_data = v4_data[(v4_data["region"] != "Unknown") & (v4_data["race"] != "Unknown")]

v4_gpa_cols = [("9th Grade", "X3TGPA9TH"), ("10th Grade", "X3TGPA10TH"),
               ("11th Grade", "X3TGPA11TH"), ("12th Grade", "X3TGPA12TH")]
v4_gpa_frames = []
for label, col in v4_gpa_cols:
    series = pd.to_numeric(v4_data[col], errors = "coerce")
    frame = pd.DataFrame({
        "region": v4_data["region"],
        "race": v4_data["race"],
        "grade": label,
        "gpa": series
    })
    v4_gpa_frames.append(frame)
v4_gpa_long = pd.concat(v4_gpa_frames, ignore_index = True)
v4_gpa_long = v4_gpa_long.dropna(subset = ["gpa"])
v4_gpa_long = v4_gpa_long[v4_gpa_long["gpa"] > 0]

v4_region_summary = v4_data.groupby("region").agg(
    stem_count = ("is_stem_major", "sum"),
    total_students = ("is_stem_major", "size"),
    stem_share = ("is_stem_major", "mean")
).reset_index()

v4_state_region_rows = []
for state_id, region in v4_state_to_region.items():
    v4_state_region_rows.append({"id": f"{state_id:02d}", "region": region})
v4_state_region_df = pd.DataFrame(v4_state_region_rows)

v4_merged_data = v4_state_region_df.merge(v4_region_summary, on = "region", how = "left")
v4_merged_data[["stem_count", "stem_share", "total_students"]] = v4_merged_data[["stem_count", "stem_share", "total_students"]].fillna(0)

v4_us_topojson_url = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"
v4_states = alt.topo_feature(v4_us_topojson_url, "states")

v4_region_select = alt.selection_point(fields = ["region"], empty = True, name = "region_select")

v4_geo_map = alt.Chart(v4_states).mark_geoshape(stroke = "white", strokeWidth = 2).encode(
    color = alt.condition(
        v4_region_select,
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
    strokeWidth = alt.condition(v4_region_select, alt.value(3), alt.value(1.5)),
    tooltip = [
        alt.Tooltip("region:N", title = "Region"),
        alt.Tooltip("stem_count:Q", title = "STEM Major Students", format = ",d")
    ]
).transform_lookup(
    lookup = "id",
    from_ = alt.LookupData(v4_merged_data, "id", ["region", "stem_share", "stem_count", "total_students"])
).add_params(v4_region_select).project(type = "albersUsa").properties(
    width = 475, height = 400,
    title = alt.TitleParams(
        text = "Geographic Distribution of STEM Major Enrollment",
        subtitle = "U.S. Census regions, 2016 cohort (HSLS:09)",
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

v4_gpa_line = alt.Chart(v4_gpa_long).transform_filter(v4_region_select).mark_line(
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
    color = alt.Color("race:N", title = "Race/Ethnicity", sort = v4_race_order,
                     scale = alt.Scale(domain = v4_race_order, range = v4_race_colors),
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
        text = "Academic Achievement Trajectories Across High School",
        subtitle = "Grade point average by race/ethnicity, grades 9 through 12",
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

viz4 = alt.hconcat(v4_geo_map, v4_gpa_line).resolve_scale(color = "independent").configure_view(
    stroke = None,
    fill = None
).properties(
    background = "transparent"
)
save_chart(viz4, "hsls_gpa_ses_trajectory.json")
