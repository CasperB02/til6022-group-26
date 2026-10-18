import os
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# 1. File paths
#gpkg_path = r"C:\Users\caspe\OneDrive\Documenten\Carrière\Universiteit\Master\Programming\Project\WijkBuurtkaart_2026_v0.gpkg"

#csv_path = r"Data\86358NED_SelectieZonderStatSymbol_20261012151433.csv"
csv_path = os.path.join('Data', '86358NED_SelectieZonderStatSymbol_20261012151433.csv')
gpkg_path = os.path.join('Data', 'WijkBuurtkaart_2026_v0.gpkg')

# 2. Load CBS neighborhood geometry
buurten = gpd.read_file(
    gpkg_path,
    layer="buurten"
)

print("Neighborhood geometry loaded.")
print("Number of neighborhood polygons:", len(buurten))
print("CRS:", buurten.crs)

# 3. Load CBS statistical data
cbs = pd.read_csv(
    csv_path,
    sep=";",
    low_memory=False
)

print("\nCBS data loaded.")
print("Number of rows:", len(cbs))

# 4. Clean region codes
cbs["Wijken en buurten"] = (
    cbs["Wijken en buurten"]
    .astype(str)
    .str.strip()
)

# 5. Keep only neighborhoods
# CBS neighborhood codes start with 'BU'
cbs_buurten = cbs[
    cbs["Wijken en buurten"].str.startswith("BU")
].copy()

print("\nNumber of CBS neighborhoods:")
print(len(cbs_buurten))

# 6. Select relevant columns
cbs_buurten = cbs_buurten[
    [
        "Wijken en buurten",
        "Regioaanduiding/Gemeentenaam (naam)",
        "Bevolking/Aantal inwoners (aantal)",
        "Bevolking/Bevolkingsdichtheid (aantal inwoners per km²)",
        "Stedelijkheid/Mate van stedelijkheid (code)",
        "Stedelijkheid/Omgevingsadressendichtheid (per km²)"
    ]
].copy()

# 7. Rename columns
cbs_buurten = cbs_buurten.rename(
    columns={
        "Wijken en buurten": "bu_code",
        "Regioaanduiding/Gemeentenaam (naam)": "gemeente",
        "Bevolking/Aantal inwoners (aantal)": "inwoners",
        "Bevolking/Bevolkingsdichtheid (aantal inwoners per km²)": "population_density",
        "Stedelijkheid/Mate van stedelijkheid (code)": "urbanity_code",
        "Stedelijkheid/Omgevingsadressendichtheid (per km²)": "address_density"
    }
)

# 8. Clean text columns
cbs_buurten["bu_code"] = (
    cbs_buurten["bu_code"]
    .astype(str)
    .str.strip()
)

cbs_buurten["gemeente"] = (
    cbs_buurten["gemeente"]
    .astype(str)
    .str.strip()
)

# 9. Convert statistical variables to numbers
numeric_columns = [
    "inwoners",
    "population_density",
    "urbanity_code",
    "address_density"
]

for column in numeric_columns:
    cbs_buurten[column] = pd.to_numeric(
        cbs_buurten[column],
        errors="coerce"
    )

# 10. Check the neighborhood codes
print("\nExample geometry neighborhood codes:")
print(buurten["bu_code"].head())

print("\nExample CBS neighborhood codes:")
print(cbs_buurten["bu_code"].head())

# 11. Merge CBS statistics with geometry
buurten_complete = buurten.merge(
    cbs_buurten,
    on="bu_code",
    how="left"
)

# 12. Check the merge
print("\nNumber of neighborhoods after merge:")
print(len(buurten_complete))

print("\nMissing population density values:")
print(
    buurten_complete["population_density"]
    .isna()
    .sum()
)

print("\nPopulation density statistics:")
print(
    buurten_complete["population_density"]
    .describe()
)

print("\nUrbanity codes:")
print(
    buurten_complete["urbanity_code"]
    .value_counts(dropna=False)
    .sort_index()
)

# 13. Remove neighborhoods without density data
buurten_plot = buurten_complete[
    buurten_complete["population_density"].notna()
].copy()

# 14. Plot population density
# Log scale cannot contain zero values
buurten_plot = buurten_complete[
    buurten_complete["population_density"] > 0
].copy()

fig, ax = plt.subplots(figsize=(10, 12))

buurten_plot.plot(
    column="population_density",
    legend=True,
    norm=LogNorm(
        vmin=buurten_plot["population_density"].min(),
        vmax=buurten_plot["population_density"].max()
    ),
    ax=ax
)

ax.set_title(
    "Population Density by Neighborhood in the Netherlands",
    fontsize=14
)

ax.axis("off")

plt.tight_layout()
plt.savefig("population_density_map.png", dpi=300, bbox_inches="tight")
plt.show()