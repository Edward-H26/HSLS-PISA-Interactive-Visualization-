import pandas as pd
import altair as alt
from config import DATA_DIR, save_chart, COUNTRY_NAME_MAP

pisa_df = pd.read_csv(DATA_DIR / "pisa_subset.csv", low_memory = False)

v9_data = pisa_df[(pisa_df["CNT"].notna()) &
                   (pisa_df["PV1MATH"].notna()) &
                   (pisa_df["PV1READ"].notna()) &
                   (pisa_df["PV1SCIE"].notna())].copy()

v9_data["Country"] = v9_data["CNT"].map(COUNTRY_NAME_MAP).fillna(v9_data["CNT"])

v9_math_scores = v9_data.groupby("Country")["PV1MATH"].mean().reset_index()
v9_math_scores.columns = ["Country", "Mean"]
v9_math_scores["Domain"] = "MATH"
v9_math_scores["Rank"] = v9_math_scores["Mean"].rank(ascending = False)

v9_read_scores = v9_data.groupby("Country")["PV1READ"].mean().reset_index()
v9_read_scores.columns = ["Country", "Mean"]
v9_read_scores["Domain"] = "READ"
v9_read_scores["Rank"] = v9_read_scores["Mean"].rank(ascending = False)

v9_scie_scores = v9_data.groupby("Country")["PV1SCIE"].mean().reset_index()
v9_scie_scores.columns = ["Country", "Mean"]
v9_scie_scores["Domain"] = "SCIE"
v9_scie_scores["Rank"] = v9_scie_scores["Mean"].rank(ascending = False)

v9_rankings_df = pd.concat([v9_math_scores, v9_read_scores, v9_scie_scores], ignore_index = True)

v9_top_countries_list = []
for domain in ["MATH", "READ", "SCIE"]:
    domain_top = v9_rankings_df[v9_rankings_df["Domain"] == domain].nsmallest(30, "Rank").copy()
    v9_top_countries_list.append(domain_top)

v9_rankings_top30 = pd.concat(v9_top_countries_list, ignore_index = True)

v9_click_domain = alt.selection_point(fields = ["Domain"], empty = True)

v9_rankings_interactive = alt.Chart(v9_rankings_top30).mark_circle(size = 60).encode(
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
    opacity = alt.condition(v9_click_domain, alt.value(1.0), alt.value(0.2)),
    tooltip = [alt.Tooltip("Country:N", title = "Country"),
              alt.Tooltip("Domain:N", title = "Domain"),
              alt.Tooltip("Mean:Q", title = "Score", format = ".1f"),
              alt.Tooltip("Rank:Q", title = "Rank", format = ".0f")]
).add_params(v9_click_domain).properties(
    width = 550,
    height = 400,
    title = {"text": "Global Comparison of PISA Scores: Top 30 Countries by Domain",
            "subtitle": "Click data point to filter",
            "fontSize": 14,
            "fontWeight": "bold",
            "color": "#FFFFFF",
            "subtitleColor": "#E0E0E0"}
)

v9_domain_avg = v9_rankings_df.groupby("Domain").agg(
    Avg_Score = ("Mean", "mean"),
    N_Countries = ("Country", "count")
).reset_index()

v9_bar_domain_avg = alt.Chart(v9_domain_avg).mark_bar(cornerRadius = 4).encode(
    y = alt.Y("Domain:N", title = "Domain"),
    x = alt.X("Avg_Score:Q", title = "Global Average Score"),
    color = alt.Color("Domain:N",
                     scale = alt.Scale(domain = ["MATH", "READ", "SCIE"],
                                      range = ["#1f77b4", "#2ca02c", "#d62728"]),
                     legend = None),
    opacity = alt.condition(v9_click_domain, alt.value(1.0), alt.value(0.3)),
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

viz9 = alt.hconcat(v9_rankings_interactive, v9_bar_domain_avg).resolve_scale(color = "independent")
save_chart(viz9, "combined_gender_stem.json")
