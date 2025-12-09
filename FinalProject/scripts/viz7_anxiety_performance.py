import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory = False)

v7_data = pisa_df[(pisa_df["ANXMAT"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["ST004D01T"].isin([1, 2]))].copy()
v7_data["Gender"] = v7_data["ST004D01T"].map({1: "Female", 2: "Male"})

v7_anxiety_terciles = v7_data["ANXMAT"].quantile([0, 0.33, 0.67, 1]).values
v7_data["Anxiety_Level"] = pd.cut(v7_data["ANXMAT"], bins = v7_anxiety_terciles,
                                   labels = ["Low", "Medium", "High"], include_lowest = True)

v7_anxiety_counts = v7_data.groupby("Anxiety_Level").size().reset_index(name = "Count")

v7_sample = v7_data.sample(n = min(10000, len(v7_data)), random_state = 42)

v7_anxiety_order = ["Low", "Medium", "High"]
v7_anxiety_colors = ["#66BB6A", "#FFA726", "#EF5350"]

v7_click_anxiety = alt.selection_point(fields = ["Anxiety_Level"], empty = True, name = "anxiety_select")

v7_left_chart = alt.Chart(v7_anxiety_counts).mark_bar(cornerRadius = 4, cursor = "pointer").encode(
    x = alt.X("Anxiety_Level:N", title = "Math Anxiety Level", sort = v7_anxiety_order,
             axis = alt.Axis(labelAngle = 0, labelFontSize = 12)),
    y = alt.Y("Count:Q", title = "Number of Students"),
    color = alt.Color("Anxiety_Level:N", title = "Anxiety Level",
                     scale = alt.Scale(domain = v7_anxiety_order, range = v7_anxiety_colors),
                     legend = alt.Legend(orient = "top")),
    opacity = alt.condition(v7_click_anxiety, alt.value(1.0), alt.value(0.5)),
    tooltip = [alt.Tooltip("Anxiety_Level:N", title = "Anxiety Level"),
              alt.Tooltip("Count:Q", title = "Students", format = ",d")]
).add_params(v7_click_anxiety).properties(
    name = "view_1",
    title = {"text": "Students by Math Anxiety Level",
            "subtitle": "Click an anxiety level to see score distribution",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 420, height = 380
)

v7_right_chart = alt.Chart(v7_sample).mark_boxplot(extent = "min-max", size = 40).encode(
    x = alt.X("Gender:N", title = "Gender",
             axis = alt.Axis(labelAngle = 0, labelFontSize = 12)),
    y = alt.Y("PV1MATH:Q", title = "Math Score (PV1MATH)",
             scale = alt.Scale(domain = [200, 700])),
    color = alt.Color("Gender:N",
                     scale = alt.Scale(domain = ["Female", "Male"], range = ["#E91E63", "#1976D2"]),
                     legend = alt.Legend(title = "Gender", orient = "top"))
).transform_filter(v7_click_anxiety).properties(
    title = {"text": "Math Score Distribution by Gender",
            "subtitle": "Filtered by anxiety level selection",
            "color": "#FFFFFF", "fontSize": 14, "subtitleColor": "#E0E0E0"},
    width = 450, height = 380
)

viz7 = alt.hconcat(v7_left_chart, v7_right_chart).resolve_scale(color = "independent")
save_chart(viz7, "pisa_anxiety_performance_heatmap.json")
