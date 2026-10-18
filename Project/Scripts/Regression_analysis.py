"""
Regression and residual analysis: population density vs. PT accessibility.

Answers sub-question 2 (how strong is the relationship, linear or non-linear?)
and creates the residuals that sub-question 4 needs (Plot_residual_map.py).

Input:
  Data/86358NED_...csv                        (CBS, population density + urbanity)
  Generated_Data/accessibility_indicator.csv  (output of OV-data.py)

Output:
  Generated_Data/residuals.csv
  Generated_Data/lowest_residuals_top20.csv
  Images/regression_scatter.png
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

# Indicator used as "PT accessibility". Total weekly departures within the
# walking distance is used because dividing by population makes small,
# sparsely populated neighborhoods score extremely high.
INDICATOR = "total_departures_per_week"

# A neighborhood is flagged as "substantially lower than expected" when its
# residual is more than this many standard deviations below the regression line.
RESIDUAL_THRESHOLD_SD = 1.0

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
        "Regioaanduiding/Gemeentenaam (naam)",
        "Bevolking/Bevolkingsdichtheid (aantal inwoners per km²)",
        "Stedelijkheid/Mate van stedelijkheid (code)",
    ]
].copy()
cbs.columns = ["bu_code", "gemeente", "density", "urbanity"]

cbs["bu_code"] = cbs["bu_code"].str.strip()
cbs["gemeente"] = cbs["gemeente"].str.strip()
cbs = cbs[cbs["bu_code"].str.startswith("BU", na=False)]
for col in ["density", "urbanity"]:
    cbs[col] = pd.to_numeric(cbs[col], errors="coerce")

access = pd.read_csv(ACCESS_FILE)
df = access.merge(cbs, on="bu_code", how="inner", validate="one_to_one")

# 3. CLEAN
n_start = len(df)
df = df[(df["density"] > 0) & (df["population"] > 0)].copy()
df = df.dropna(subset=["density", "urbanity", INDICATOR])
df["urbanity"] = df["urbanity"].astype(int)
print(f"Neighborhoods used: {len(df)} (dropped {n_start - len(df)} without density/population)")
print(f"Neighborhoods with zero departures: {(df[INDICATOR] == 0).sum()}")

# Data check: a neighborhood with stops within walking distance but zero departures
# usually means the stop frequencies are incomplete, not that there is no service
suspicious = ((df["stops_within_distance"] > 0) & (df[INDICATOR] == 0)).sum()
print(f"Neighborhoods with stops nearby but zero departures: {suspicious}")
if suspicious > 0.01 * len(df):
    print("WARNING: check stop_frequencies.csv, the residuals below may be unreliable.")

# log10(1 + y) keeps neighborhoods without any service in the data (log of 0 is undefined)
df["log_density"] = np.log10(df["density"])
df["log_access"] = np.log10(1 + df[INDICATOR])

x_log = df["log_density"].to_numpy()
x_lin = df["density"].to_numpy()
y = df["log_access"].to_numpy()

# 4. CORRELATION
pearson_r, _ = stats.pearsonr(x_log, y)
spearman_rho, _ = stats.spearmanr(df["density"], df[INDICATOR])
print(f"\nPearson r (log density vs log accessibility): {pearson_r:.3f}")
print(f"Spearman rho (raw density vs raw accessibility): {spearman_rho:.3f}")


# 5. COMPARE MODELS (same dependent variable, so the R-squared values are comparable)
def r_squared(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    return 1 - ss_res / ss_tot


models = {}

# Model 1: linear in density
coef1 = np.polyfit(x_lin, y, 1)
models["Linear (density)"] = (np.polyval(coef1, x_lin), coef1)

# Model 2: log-log (power law)
coef2 = np.polyfit(x_log, y, 1)
models["Log-log (power law)"] = (np.polyval(coef2, x_log), coef2)

# Model 3: log-log with a quadratic term (non-linear in log space)
coef3 = np.polyfit(x_log, y, 2)
models["Log-log quadratic"] = (np.polyval(coef3, x_log), coef3)

print("\nModel comparison (dependent variable: log10(1 + departures per week))")
r2 = {}
for name, (pred, coef) in models.items():
    r2[name] = r_squared(y, pred)
    print(f"  {name:<22} R2 = {r2[name]:.3f}")

best_model = max(r2, key=r2.get)
print(f"Best fit: {best_model}")

# Residuals come from the log-log model: the simplest model that captures the
# curved relationship, so the residual is easy to interpret
# (a residual of -1 means ten times fewer departures than expected).
df["predicted_log_access"] = models["Log-log (power law)"][0]
df["residual"] = df["log_access"] - df["predicted_log_access"]
df["residual_z"] = df["residual"] / df["residual"].std()
df["low_for_density"] = df["residual_z"] < -RESIDUAL_THRESHOLD_SD

print(f"\nResidual SD: {df['residual'].std():.3f}")
print(
    f"Neighborhoods more than {RESIDUAL_THRESHOLD_SD} SD below the line: "
    f"{df['low_for_density'].sum()} ({df['low_for_density'].mean():.1%})"
)

# 6. EXPORT TABLES
out_cols = [
    "bu_code", "bu_naam", "gemeente", "population", "density", "urbanity",
    "stops_within_distance", INDICATOR, "predicted_log_access",
    "residual", "residual_z", "low_for_density",
]
(ROOT / "Generated_Data").mkdir(exist_ok=True)
df[out_cols].to_csv(ROOT / "Generated_Data" / "residuals.csv", index=False)

# Top 20: lowest residuals, but only neighborhoods with a meaningful population
# so that tiny industrial areas do not dominate the list
top20 = (
    df[df["population"] >= 500]
    .nsmallest(20, "residual")[
        ["bu_naam", "gemeente", "population", "density", INDICATOR, "residual_z"]
    ]
)
top20.to_csv(ROOT / "Generated_Data" / "lowest_residuals_top20.csv", index=False)
print("\n20 neighborhoods (>= 500 residents) with the lowest accessibility given their density:")
print(top20.to_string(index=False))

# 7. FIGURE: SCATTER + FITS
# (the linear-in-density model is only reported in the table above: on a log-log
# plot it shoots up exponentially and hides the other two fits)
(ROOT / "Images").mkdir(exist_ok=True)
fig, ax = plt.subplots(figsize=(9, 6))

ax.scatter(
    df["density"], df[INDICATOR] + 1,
    s=4, alpha=0.2, color="#2b6cb0", linewidths=0, rasterized=True,
    label="Neighborhoods",
)

grid_log = np.linspace(x_log.min(), x_log.max(), 300)
grid = 10**grid_log
ax.plot(grid, 10 ** np.polyval(coef2, grid_log), color="#c53030", lw=2,
        label=f"Log-log fit (R² = {r2['Log-log (power law)']:.2f})")
ax.plot(grid, 10 ** np.polyval(coef3, grid_log), color="#2f855a", lw=2, ls="--",
        label=f"Log-log quadratic (R² = {r2['Log-log quadratic']:.2f})")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Population density (inhabitants per km², log scale)")
ax.set_ylabel("Departures per week within walking distance (+1, log scale)")
ax.set_title("Population density vs. public transport accessibility", fontweight="bold")
ax.legend(frameon=False, loc="upper left")
ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(ROOT / "Images" / "regression_scatter.png", dpi=200, facecolor="white")
plt.close(fig)

print("\nSaved: residuals.csv, lowest_residuals_top20.csv, regression_scatter.png")
