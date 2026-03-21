# HSLS-PISA Interactive Visualization

An interactive data visualization showcase analyzing educational datasets from the High School Longitudinal Study of 2009 (HSLS:09) and the Programme for International Student Assessment (PISA 2022). The project ships 9 linked Vega-Lite visualizations across 13 panels, responsive navigation, and a glassmorphism-inspired presentation layer.

## Quick Start

Serve locally with any static file server:

```bash
python3 -m http.server 4008
```

Then open http://127.0.0.1:4008/ in your browser.

## Directory Structure

```
├── index.html              Main showcase (13 panels, 9 visualizations)
├── 404.html                Error page
├── icon.svg                Site icon
├── .nojekyll               GitHub Pages static serving flag
│
├── assets/
│   ├── css/style.css       Glassmorphism styling and animations
│   ├── js/main.js          Navigation, particles, Vega-Embed loading
│   └── json/               9 Vega-Lite chart specifications
│
├── scripts/                Python visualization generators
│   ├── config.py           Shared config (dark theme, country maps)
│   └── viz1-viz9_*.py      Individual chart generators (Altair → JSON)
│
├── data/                   Source datasets
│   ├── hsls_subset.csv     HSLS:09 processed data
│   ├── pisa_subset.csv     PISA 2022 processed data
│   ├── data_subset.py      HSLS subset generator
│   └── data_subset_PISA.py PISA subset generator
│
├── src/
│   └── data_loader.py      Data loading and processing utility
│
├── config/
│   ├── dataset.ini         HSLS dataset field mappings
│   └── data_process.ini    Data transformation rules
│
├── codebook/               Dataset reference documentation
└── python_notebooks/       Maintained HSLS/PISA analysis notebook
```

## Visualizations

The showcase contains 9 interactive Vega-Lite visualizations organized into 4 sections:

| Section | Visualizations |
|---------|---------------|
| Overview | Introduction, Conclusion, HSLS:09 Dataset, PISA 2022 Dataset |
| Family and Resources | Parental Education and STEM, Digital Resources and Immigration, Internet Usage and Gender |
| Regional and Economic | Regional STEM Enrollment, SES and Efficacy, Technology and STEM Interest |
| Wellbeing and Outcomes | Math Anxiety and Belonging, Regional Achievement, School Belonging and Immigration |

## Regenerating Visualizations

The Python scripts in `scripts/` generate the Vega-Lite JSON specifications from the source data:

```bash
pip install altair pandas vega_datasets
cd scripts
python viz1_parental_education_income_stem.py
```

Each script reads from `data/hsls_subset.csv` or `data/pisa_subset.csv` and writes its output to `assets/json/`.

## Data Sources

- **HSLS:09**: High School Longitudinal Study of 2009, National Center for Education Statistics
- **PISA 2022**: Programme for International Student Assessment, OECD

## Navigation

- **Responsive layout**: The site adapts across desktop, tablet, and mobile widths
- **Sidebar**: Click tabs to switch between visualization sections
- **Keyboard**: Arrow keys to navigate between panels
- **Mouse wheel**: Scroll vertically within panels, horizontally at edges
- **Touch**: Swipe left/right to navigate between panels
