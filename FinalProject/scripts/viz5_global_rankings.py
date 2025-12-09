import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart, COUNTRY_NAME_MAP

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory = False)

v5_data = pisa_df[(pisa_df["CNT"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["PV1READ"].notna()) &
                   (pisa_df["PV1SCIE"].notna())].copy()

v5_data["Country"] = v5_data["CNT"].map(COUNTRY_NAME_MAP).fillna(v5_data["CNT"])

v5_math_scores = v5_data.groupby("Country")["PV1MATH"].mean().reset_index()
v5_math_scores.columns = ["Country", "Mean"]
v5_math_scores["Domain"] = "MATH"
v5_math_scores["Rank"] = v5_math_scores["Mean"].rank(ascending = False)

v5_read_scores = v5_data.groupby("Country")["PV1READ"].mean().reset_index()
v5_read_scores.columns = ["Country", "Mean"]
v5_read_scores["Domain"] = "READ"
v5_read_scores["Rank"] = v5_read_scores["Mean"].rank(ascending = False)

v5_scie_scores = v5_data.groupby("Country")["PV1SCIE"].mean().reset_index()
v5_scie_scores.columns = ["Country", "Mean"]
v5_scie_scores["Domain"] = "SCIE"
v5_scie_scores["Rank"] = v5_scie_scores["Mean"].rank(ascending = False)

v5_rankings_df = pd.concat([v5_math_scores, v5_read_scores, v5_scie_scores], ignore_index = True)

v5_top_countries_list = []
for domain in ["MATH", "READ", "SCIE"]:
    domain_top = v5_rankings_df[v5_rankings_df["Domain"] == domain].nsmallest(30, "Rank").copy()
    v5_top_countries_list.append(domain_top)

v5_rankings_top30 = pd.concat(v5_top_countries_list, ignore_index = True)

v5_click_domain = alt.selection_point(fields = ["Domain"], empty = True)

v5_rankings_interactive = alt.Chart(v5_rankings_top30).mark_circle(size = 60).encode(
    x = alt.X("Country:N",
             sort = alt.EncodingSortField(field = "Mean", order = "descending"),
             title = "Country",
             axis = alt.Axis(labelAngle = -45, labelFontSize = 10, titleFontSize = 12)),
    y = alt.Y("Mean:Q",
             title = "Score",
             scale = alt.Scale(domain = [460, 580])),
    color = alt.Color("Domain:N",
                     title = "Domain",
                     scale = alt.Scale(domain = ["MATH", "READ", "SCIE"],
                                      range = ["#1f77b4", "#2ca02c", "#d62728"]),
                     legend = alt.Legend(titleFontSize = 13, labelFontSize = 12)),
    opacity = alt.condition(v5_click_domain, alt.value(1.0), alt.value(0.2)),
    tooltip = [alt.Tooltip("Country:N", title = "Country"),
              alt.Tooltip("Domain:N", title = "Domain"),
              alt.Tooltip("Mean:Q", title = "Score", format = ".1f"),
              alt.Tooltip("Rank:Q", title = "Rank", format = ".0f")]
).add_params(v5_click_domain).properties(
    width = 550,
    height = 400,
    title = {"text": "Global Comparison of PISA Scores: Top 30 Countries by Domain",
            "subtitle": "Click data point to filter",
            "fontSize": 14,
            "fontWeight": "bold",
            "color": "#FFFFFF",
            "subtitleColor": "#E0E0E0"}
)

v5_domain_avg = v5_rankings_df.groupby("Domain").agg(
    Avg_Score = ("Mean", "mean"),
    N_Countries = ("Country", "count")
).reset_index()

v5_bar_domain_avg = alt.Chart(v5_domain_avg).mark_bar(cornerRadius = 4).encode(
    y = alt.Y("Domain:N", title = "Domain"),
    x = alt.X("Avg_Score:Q", title = "Global Average Score"),
    color = alt.Color("Domain:N",
                     scale = alt.Scale(domain = ["MATH", "READ", "SCIE"],
                                      range = ["#1f77b4", "#2ca02c", "#d62728"]),
                     legend = None),
    opacity = alt.condition(v5_click_domain, alt.value(1.0), alt.value(0.3)),
    tooltip = [alt.Tooltip("Domain:N", title = "Domain"),
              alt.Tooltip("Avg_Score:Q", title = "Global Average", format = ".1f"),
              alt.Tooltip("N_Countries:Q", title = "Countries")]
).properties(
    width = 250,
    height = 400,
    title = {"text": "Global Averages",
            "fontSize": 14,
            "fontWeight": "bold",
            "color": "#FFFFFF"}
)

viz5 = alt.hconcat(v5_rankings_interactive, v5_bar_domain_avg).resolve_scale(color = "independent")
save_chart(viz5, "combined_gender_stem.json")
