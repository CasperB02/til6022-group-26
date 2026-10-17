"""
Map of the regression residuals (sub-question 4).

Shows which neighborhoods have less public transport than expected given their
population density. Run Regression_analysis.py first: it creates residuals.csv.
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

# 1. File paths
ROOT = Path(__file__).resolve().parents[2]

geometry_file = ROOT / "Data" / "WijkBuurtkaart_2026_v0.gpkg"
residuals_file = ROOT / "Generated_Data" / "residuals.csv"
output_file = ROOT / "Images" / "residual_map.png"

# 2. Load neighborhood geometry (land only, same filter as Plot_accessibility_map.py)
buurten = gpd.read_file(geometry_file, layer="buurten")
buurten = buurten[["bu_code", "water", "geometry"]].copy()
buurten["water"] = buurten["water"].astype("string").str.strip().str.upper()
buurten = buurten.loc[buurten["water"].eq("NEE"), ["bu_code", "geometry"]].copy()

# 3. Merge residuals with geometry
residuals = pd.read_csv(residuals_file)
nl_map = buurten.merge(
    residuals[["bu_code", "residual_z"]],
    on="bu_code",
    how="left",
    validate="one_to_one",
)

# 4. Create the map
# Diverging scale centred on 0: red = less PT than expected, blue = more than expected
fig, ax = plt.subplots(figsize=(12, 14))

cmap = "RdBu"
norm = TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3)

nl_map.plot(
    column="residual_z",
    cmap=cmap,
    norm=norm,
    ax=ax,
    linewidth=0,
    missing_kwds={"color": "lightgrey"},
)

sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.65, pad=0.02, extend="both")
cbar.set_label("Residual (standard deviations from the regression line)", fontsize=11)

ax.set_title(
    "Public Transport Accessibility Relative to Population Density",
    fontsize=17,
    fontweight="bold",
    pad=20,
)
ax.text(
    0.02, 0.02,
    "Red: less public transport than expected for this density\n"
    "Blue: more than expected   Grey: no density data",
    transform=ax.transAxes, fontsize=10, va="bottom",
)
ax.axis("off")

# 5. Save the map
output_file.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(output_file, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

print(f"Map saved to: {output_file}")
print(f"Neighborhoods mapped: {len(nl_map)}")
