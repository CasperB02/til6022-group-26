import os
import pandas as pd
import geopandas as gpd

# 1. Define file paths
stops_file = os.path.join('Data', 'stops.txt')
buurten_file = os.path.join('Data', 'WijkBuurtkaart_2026_v0.gpkg')
cbs_file = os.path.join('Data', '86358NED_SelectieZonderStatSymbol_20261012151433.csv')
weekly_frequency_file = os.path.join('Data', 'stop_frequency_per_week.csv')
Distance_M = 500

# 2. Load buurt geometry
buurten = gpd.read_file(buurten_file, layer="buurten")
buurten = buurten[["bu_code","bu_naam", "geometry"]]
buurten["bu_code"] = buurten["bu_code"].astype(str).str.strip()


# 3. Load CBS population and normalize its columns
cbs = pd.read_csv(cbs_file, sep=";", dtype="string")
code_col = "Regioaanduiding/Codering (code)"
population_col = "Bevolking/Aantal inwoners (aantal)"

population = cbs[[code_col, population_col]].copy()
population.columns = ["bu_code", "population"]
population["bu_code"] = population["bu_code"].str.strip()
population = population[population["bu_code"].str.startswith("BU", na=False)]
population["population"] = pd.to_numeric(population["population"], errors="coerce")
population = population.dropna(subset=["population"])
assert population["bu_code"].is_unique

# 4. Load GTFS stop points; keep boarding stops with coordinates
stops = pd.read_csv(stops_file, dtype={"stop_id": "string"})
stops = stops.dropna(subset=["stop_id", "stop_lon", "stop_lat"])
if "location_type" in stops.columns:
    location_type = pd.to_numeric(stops["location_type"], errors="coerce").fillna(0)
    stops = stops.loc[location_type == 0].copy()

stops["stop_lon"] = pd.to_numeric(stops["stop_lon"], errors="coerce")
stops["stop_lat"] = pd.to_numeric(stops["stop_lat"], errors="coerce")
stops = stops.dropna(subset=["stop_lon", "stop_lat"])
stop_points = gpd.GeoDataFrame(
    stops[["stop_id"]].copy(),
    geometry=gpd.points_from_xy(stops["stop_lon"], stops["stop_lat"]),
    crs="EPSG:4326",
)

# 5. Reproject to metres and find stops within the buurt buffer
stop_points = stop_points.to_crs(buurten.crs)
buurt_buffers = buurten[["bu_code", "geometry"]].copy()
buurt_buffers["geometry"] = buurt_buffers.geometry.buffer(Distance_M)

matches = gpd.sjoin(
    stop_points,
    buurt_buffers,
    how="inner",
    predicate="within",
)[["bu_code", "stop_id"]].drop_duplicates()

# 6. Load average weekly service frequency by stop ID
if not os.path.isfile(weekly_frequency_file):
    raise FileNotFoundError(
        f"Weekly frequency file not found: {weekly_frequency_file}. "
        "Expected columns: stop_id, average_stops_per_week."
    )

stop_frequency = pd.read_csv(
    weekly_frequency_file,
    dtype={"stop_id": "string"},
)
required_frequency_columns = {"stop_id", "average_stops_per_week"}
missing_frequency_columns = required_frequency_columns - set(stop_frequency.columns)
if missing_frequency_columns:
    raise ValueError(
        f"Weekly frequency file is missing columns: {sorted(missing_frequency_columns)}"
    )

stop_frequency = stop_frequency[["stop_id", "average_stops_per_week"]].copy()
stop_frequency["stop_id"] = stop_frequency["stop_id"].str.strip()
stop_frequency["average_stops_per_week"] = pd.to_numeric(
    stop_frequency["average_stops_per_week"],
    errors="coerce",
)

invalid_stop_ids = stop_frequency["stop_id"].isna() | stop_frequency["stop_id"].eq("")
if invalid_stop_ids.any():
    raise ValueError("The weekly frequency file contains missing or blank stop IDs")
if stop_frequency["average_stops_per_week"].isna().any():
    raise ValueError("The weekly frequency file contains missing or non-numeric frequencies")
if stop_frequency["stop_id"].duplicated().any():
    raise ValueError("The weekly frequency file must have one row per stop_id")
if (stop_frequency["average_stops_per_week"] < 0).any():
    raise ValueError("Average stops per week cannot be negative")

# 7. Join weekly frequency to nearby stops, then aggregate per buurt
matches["stop_id"] = matches["stop_id"].astype("string").str.strip()
nearby_service = matches.merge(
    stop_frequency,
    on="stop_id",
    how="left",
    validate="many_to_one",
)
if nearby_service["average_stops_per_week"].isna().any():
    missing_stop_ids = (
        nearby_service.loc[
            nearby_service["average_stops_per_week"].isna(), "stop_id"
        ]
        .drop_duplicates()
        .head(10)
        .tolist()
    )
    raise ValueError(
        "The weekly frequency file has no valid frequency for nearby stop IDs, "
        f"for example: {missing_stop_ids}"
    )

by_buurt = nearby_service.groupby("bu_code").agg(
    stops_within_distance=("stop_id", "nunique"),
    total_average_stops_per_week=("average_stops_per_week", "sum"),
).reset_index()

# 8. Add population and calculate the normalized indicator
result = buurten[["bu_code", "bu_naam"]].merge(
    population, on="bu_code", how="left"
).merge(
    by_buurt, on="bu_code", how="left"
)
result[["stops_within_distance", "total_average_stops_per_week"]] = result[
    ["stops_within_distance", "total_average_stops_per_week"]
].fillna(0)
result["stops_within_distance"] = result["stops_within_distance"].astype(int)
result["average_stops_per_week_per_1000_residents"] = (
    1000 * result["total_average_stops_per_week"]
    / result["population"].where(result["population"] > 0)
)

# 9. Export the buurt-level results
matches.to_csv(os.path.join('Data', "buurt_stop_matches.csv"), index=False)
result.to_csv(os.path.join('Data', "accessibility_indicator.csv"), index=False)