
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

# 1. File paths
ROOT = Path(__file__).resolve().parents[2]

geometry_file = ROOT / "Data" / "WijkBuurtkaart_2026_v0.gpkg"
accessibility_file = ROOT / "Generated_Data" / "accessibility_indicator.csv"
output_file = ROOT / "Images" / "accessibility_map.png"

# 2. Select the indicator to visualize
indicator = "departures_per_week_per_1000_residents"

# Alternative:
# indicator = "total_departures_per_week"

# 3. Load neighborhood geometry
buurten = gpd.read_file(geometry_file, layer="buurten")
buurten = buurten[["bu_code", "water", "geometry"]].copy()
buurten["water"] = buurten["water"].astype("string").str.strip().str.upper()
buurten = buurten.loc[
    buurten["water"].eq("NEE"),
    ["bu_code", "geometry"],
].copy()

# 4. Load accessibility data
accessibility = pd.read_csv(accessibility_file)

# 5. Merge data with geometry
nl_map = buurten.merge(
    accessibility[["bu_code", "population", indicator]],
    on="bu_code",
    how="left",
    validate="one_to_one"
)

# 6. Prepare values for visualization
nl_map[indicator] = pd.to_numeric(
    nl_map[indicator], errors="coerce"
)

# Limit extreme outliers to the 98th percentile
max_value = nl_map[indicator].quantile(0.98)

# Logarithmic color scale (including zero)
nl_map["plot_value"] = np.log1p(
    nl_map[indicator].clip(lower=0, upper=max_value)
)

# 7. Create the map
fig, ax = plt.subplots(figsize=(12, 14))

cmap = "YlGnBu"
norm = Normalize(vmin=0, vmax=np.log1p(max_value))

nl_map.plot(
    column="plot_value",
    cmap=cmap,
    norm=norm,
    ax=ax,
    linewidth=0,
    missing_kwds={"color": "orange"}
)

# 8. Colorbar with original indicator values
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])

cbar = fig.colorbar(
    sm, ax=ax, shrink=0.65, pad=0.02
)

ticks = [0, 100, 1000, 10000, 100000]
ticks = [x for x in ticks if x < max_value]
ticks.append(max_value)

cbar.set_ticks(np.log1p(ticks))
cbar.set_ticklabels(
    [f"{x:,.0f}" for x in ticks[:-1]]
    + [f"≥{max_value:,.0f}"]
)

cbar.set_label(
    "Weekly departures per 1,000 residents",
    fontsize=11
)

# 9. Styling
ax.set_title(
    "Public Transport Accessibility in the Netherlands",
    fontsize=17,
    fontweight="bold",
    pad=20
)

ax.axis("off")

# 10. Save the map
output_file.parent.mkdir(parents=True, exist_ok=True)

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.close(fig)

print(f"Map saved to: {output_file}")
print(f"Neighborhoods mapped: {len(nl_map)}")
