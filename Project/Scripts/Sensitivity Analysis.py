from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
from scipy import stats

# 1. SETTINGS & FILE PATHS (Aligned with Regression_analysis.py and OV-data.py)
ROOT = Path(__file__).resolve().parents[2]

stops_file = ROOT / "Data" / "stops.txt"
buurten_file = ROOT / "Data" / "WijkBuurtkaart_2026_v0.gpkg"
cbs_file = ROOT / "Data" / "86358NED_SelectieZonderStatSymbol_20261012151433.csv"
weekly_frequency_file = ROOT / "Generated_Data" / "stop_frequencies.csv"