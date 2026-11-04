# The Mobility Divide
A quantitative analysis of the relationship between population density and public transport supply in the Netherlands.

## Group 26
* Casper Bosman
* Wouter van Aalderen
* Maarten van Dijk
* Zef Nijmeijer
* Casper Sanders

## Project Overview
This repository contains the final research project and data processing pipeline for **Group 26** as part of **TIL6022 Python Programming (2026)** at Delft University of Technology.

The study evaluates the spatial relationship between public transport accessibility (derived from national GTFS timetable schedules) and population density (retrieved from CBS neighborhood statistics) across 14,041 Dutch neighborhoods (*buurten*), identifying structural service disparities between urban and rural environments.

## Repository Structure
* `project_template.ipynb`: Main Jupyter Notebook with full research narrative, empirical models, tables, and conclusions.
* `project_template.html`: Standalone HTML export of the complete notebook.
* `Project/Scripts/`: Python processing and analysis scripts:
  * `Departures_per_week.py` & `OV-data.py`: GTFS extraction and stop frequency calculations.
  * `CBS_population_density.py`: CBS StatLine demographics and neighborhood geometries.
  * `Regression_analysis.py`: Log-log OLS and polynomial modeling.
  * `Urban_rural_comparison.py`: CBS urbanity segmentation (Classes 1–5) and boxplot generation.
  * `Sensitivity_Analysis.py`: Catchment buffer distance evaluations and CBS demographic checking.
  * `Plot_accessibility_map.py` & `Plot_residual_map.py`: Spatial visualization scripts.
* `Images/`: Generated visualization outputs:
  * `accessibility_map.png`: National public transport accessibility distribution.
  * `regression_scatter.png`: Density vs. accessibility regression curves.
  * `sensitivity_regression_lines.png`: Multi-buffer sensitivity comparisons.
  * `urbanity_boxplot.png`: Distribution of weekly departures across CBS urbanity tiers.
  * `residual_map.png`: Spatial distribution of over- and underserved neighborhoods.
* `Data/`: Source datasets (CBS boundary GeoPackage, GTFS feeds, demographic tables).
* `Generated_Data/`: Processed intermediate datasets (`accessibility_indicator.csv`, `residuals.csv`, `stop_frequencies.csv`, `lowest_residuals_top20.csv`, `urbanity_summary.csv`).

## Reproduction Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CasperB02/til6022-group-26.git
   cd til6022-group-26
   ```

2. **Activate the course Conda environment:**
   ```bash
   conda activate TIL6022
   ```

3. **Pull binary spatial geometries via Git LFS:**
   ```bash
   git lfs install
   git lfs pull
   ```

4. **Execute the analytical pipeline scripts:**
   ```bash
   python Project/Scripts/Regression_analysis.py
   python Project/Scripts/Urban_rural_comparison.py
   python Project/Scripts/Sensitivity_Analysis.py
   python Project/Scripts/Plot_accessibility_map.py
   python Project/Scripts/Plot_residual_map.py
   ```

5. **View and export the notebook:**
   Open `project_template.ipynb` to inspect the full report and visualizations, or regenerate the HTML export via:
   ```bash
   python -m nbconvert --to html project_template.ipynb
   ```
