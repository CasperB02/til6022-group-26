# The Mobility Divide
A quantitative analysis of the relationship between population density and public transport supply in the Netherlands.

## Group 26
* Casper Bosman
* Wouter van Aalderen
* Maarten van Dijk
* Zef Nijmeijer
* Casper Sanders

## Project Overview
This repository contains the final research project and data processing pipeline for **Group 26** as part of **TIL6022 Python Programming (2026)** at Delft University of Technology[span_2](start_span)[span_2](end_span)[span_3](start_span)[span_3](end_span). 

The study evaluates the spatial relationship between public transport accessibility (derived from national GTFS timetable schedules) and population density (retrieved from CBS neighborhood statistics) across 14,041 Dutch neighborhoods (*buurten*), identifying structural service disparities between urban and rural environments[span_4](start_span)[span_4](end_span)[span_5](start_span)[span_5](end_span).

## Repository Structure
* `project_template.ipynb`: Main Jupyter Notebook with full research narrative, empirical models, tables, and conclusions[span_6](start_span)[span_6](end_span)[span_7](start_span)[span_7](end_span).
* `project_template.html`: Standalone HTML export of the complete notebook[span_8](start_span)[span_8](end_span).
* `Project/Scripts/`: Python processing and analysis scripts:
  * `Departures_per_week.py` & `OV-data.py`: GTFS extraction and stop frequency calculations[span_9](start_span)[span_9](end_span).
  * `CBS_population_density.py`: CBS StatLine demographics and neighborhood geometries[span_10](start_span)[span_10](end_span).
  * `Regression_analysis.py`: Log-log OLS and polynomial modeling[span_11](start_span)[span_11](end_span).
  * `Urban_rural_comparison.py`: CBS urbanity segmentation (Classes 1–5) and boxplot generation[span_12](start_span)[span_12](end_span).
  * `Sensitivity_Analysis.py`: Catchment buffer distance evaluations and CBS income data detection[span_13](start_span)[span_13](end_span).
  * `Plot_accessibility_map.py` & `Plot_residual_map.py`: Spatial visualization scripts[span_14](start_span)[span_14](end_span)[span_15](start_span)[span_15](end_span).
* `Images/`: Generated visualization outputs:
  * `accessibility_map.png`: National public transport accessibility distribution[span_16](start_span)[span_16](end_span).
  * `regression_scatter.png`: Density vs. accessibility regression curves[span_17](start_span)[span_17](end_span).
  * `sensitivity_regression_lines.png`: Multi-buffer sensitivity comparisons[span_18](start_span)[span_18](end_span).
  * `urbanity_boxplot.png`: Distribution of weekly departures across CBS urbanity tiers.
  * `residual_map.png`: Spatial distribution of over- and underserved neighborhoods[span_19](start_span)[span_19](end_span)[span_20](start_span)[span_20](end_span).
* `Data/`: Source datasets (CBS boundary GeoPackage, GTFS feeds, demographic tables)[span_21](start_span)[span_21](end_span).
* `Generated_Data/`: Processed intermediate datasets (`accessibility_indicator.csv`, `residuals.csv`, `stop_frequencies.csv`, `lowest_residuals_top20.csv`, `urbanity_summary.csv`)[span_22](start_span)[span_22](end_span).

## Reproduction Steps

### 1. Clone the repository
```bash
git clone [https://github.com/CasperB02/til6022-group-26.git](https://github.com/CasperB02/til6022-group-26.git)
cd til6022-group-26
