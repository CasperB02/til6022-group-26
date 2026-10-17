"""
Urban versus rural comparison of PT accessibility.

Answers sub-question 3: does the relationship between population density and
PT accessibility differ between urban and rural neighborhoods?

Urban/rural follows the CBS degree of urbanity (1 = very urban, 5 = not urban).

Input:
  Data/86358NED_...csv                        (CBS, density + urbanity)
  Generated_Data/accessibility_indicator.csv  (output of OV-data.py)

Output:
  Generated_Data/urbanity_summary.csv
  Images/urbanity_boxplot.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# 1. SETTINGS
ROOT = Path(__file__).resolve().parents[2]
CBS_FILE = ROOT / "Data" / "86358NED_SelectieZonderStatSymbol_20261012151433.csv"
ACCESS_FILE = ROOT / "Generated_Data" / "accessibility_indicator.csv"

INDICATOR = "total_departures_per_week"

URBANITY_LABELS = {
    1: "1 Very urban\n(>2,500/km²)",
    2: "2 Urban\n(1,500-2,500)",
    3: "3 Moderately\nurban\n(1,000-1,500)",
    4: "4 Slightly urban\n(500-1,000)",
    5: "5 Not urban\n(<500)",
}

# 2. LOAD AND MERGE
cbs = pd.read_csv(CBS_FILE, sep=";", dtype="string")
cbs.columns = [c.strip() for c in cbs.columns]

cbs = cbs[
    [
        "Regioaanduiding/Codering (code)",
        "Bevolking/Bevolkingsdichtheid (aantal inwoners per km²)",
        "Stedelijkheid/Mate van stedelijkheid (code)",
    ]
].copy()
cbs.columns = ["bu_code", "density", "urbanity"]

cbs["bu_code"] = cbs["bu_code"].str.strip()
cbs = cbs[cbs["bu_code"].str.startswith("BU", na=False)]
for col in ["density", "urbanity"]:
    cbs[col] = pd.to_numeric(cbs[col], errors="coerce")

access = pd.read_csv(ACCESS_FILE)
df = access.merge(cbs, on="bu_code", how="inner", validate="one_to_one")

# 3. CLEAN
df = df[(df["density"] > 0) & (df["population"] > 0)].dropna(
    subset=["density", "urbanity", INDICATOR]
).copy()
df["urbanity"] = df["urbanity"].astype(int)

# log10(1 + y) keeps neighborhoods without any service in the data
df["log_density"] = np.log10(df["density"])
df["log_access"] = np.log10(1 + df[INDICATOR])

print(f"Neighborhoods used: {len(df)}")

# 4. REGRESSION PER URBANITY CLASS
rows = []
for code in sorted(URBANITY_LABELS):
    g = df[df["urbanity"] == code]
    slope, intercept, r, p, _ = stats.linregress(g["log_density"], g["log_access"])
    rows.append(
        {
            "urbanity": code,
            "n": len(g),
            "median_density": g["density"].median(),
            "median_departures_per_week": g[INDICATOR].median(),
            "share_zero_departures": (g[INDICATOR] == 0).mean(),
            "slope": slope,
            "r_squared": r**2,
            "p_value": p,
        }
    )

summary = pd.DataFrame(rows)
print("\nLog-log regression per urbanity class")
print(summary.round(3).to_string(index=False))

# 5. DOES ACCESSIBILITY DIFFER BETWEEN THE CLASSES?
groups = [g["log_access"].to_numpy() for _, g in df.groupby("urbanity")]
kw = stats.kruskal(*groups)
print(f"\nKruskal-Wallis test across urbanity classes: H = {kw.statistic:.1f}, p = {kw.pvalue:.2e}")

# Very urban versus not urban
very_urban = df.loc[df["urbanity"] == 1, INDICATOR].median()
not_urban = df.loc[df["urbanity"] == 5, INDICATOR].median()
print(f"Median departures per week: very urban {very_urban:,.0f}, not urban {not_urban:,.0f}")

# 6. EXPORT TABLE
(ROOT / "Generated_Data").mkdir(exist_ok=True)
summary.to_csv(ROOT / "Generated_Data" / "urbanity_summary.csv", index=False)

# 7. FIGURE: BOXPLOT PER URBANITY CLASS
(ROOT / "Images").mkdir(exist_ok=True)
fig, ax = plt.subplots(figsize=(9, 6))

data = [df.loc[df["urbanity"] == c, INDICATOR] + 1 for c in sorted(URBANITY_LABELS)]
bp = ax.boxplot(
    data,
    labels=[URBANITY_LABELS[c] for c in sorted(URBANITY_LABELS)],
    showfliers=False,
    patch_artist=True,
    medianprops={"color": "black"},
)
for patch in bp["boxes"]:
    patch.set_facecolor("#90cdf4")

ax.set_yscale("log")
ax.set_ylabel("Departures per week within walking distance (+1, log scale)")
ax.set_title("PT accessibility by degree of urbanity (CBS)", fontweight="bold")
ax.grid(axis="y", alpha=0.2)

fig.tight_layout()
fig.savefig(ROOT / "Images" / "urbanity_boxplot.png", dpi=200, facecolor="white")
plt.close(fig)

print("\nSaved: urbanity_summary.csv, urbanity_boxplot.png")
