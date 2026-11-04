import pandas as pd
from pathlib import Path
from collections import Counter

# 1. SETTINGS
DATA = Path(__file__).resolve().parents[2] / "data"
GENERATED_DATA = Path(__file__).resolve().parents[2] / "Generated_Data"

START = "2026-10-26"
END = "2026-11-01"

# 2. LOAD CALENDAR
calendar = pd.read_csv(
    DATA / "calendar_dates.txt",
    dtype=str
)

week_dates = set(
    pd.date_range(START, END).strftime("%Y%m%d")
)

week = calendar[calendar["date"].isin(week_dates)]

if week["date"].nunique() != 7:
    raise ValueError("Selected week is incomplete!")

if not week["exception_type"].eq("1").all():
    raise ValueError("Unexpected calendar exception type!")

service_days = (
    week.drop_duplicates(["service_id", "date"])
    .groupby("service_id")
    .size()
)

# 3. IDENTIFY FLEX ROUTES
routes = pd.read_csv(
    DATA / "routes.txt",
    dtype=str
)

flex = (
    routes["route_short_name"].str.contains(
        "flex", case=False, na=False
    )
    |
    routes["route_long_name"].str.contains(
        "flex", case=False, na=False
    )
)

flex_ids = set(routes.loc[flex, "route_id"])

print("Excluded flex routes:", len(flex_ids))

# 4. CALCULATE WEEKLY RUNS PER TRIP
trips = pd.read_csv(
    DATA / "trips.txt",
    usecols=["trip_id", "service_id", "route_id"],
    dtype=str
)

# Identify trips belonging to Flex routes
flex_trip_ids = set(
    trips.loc[trips["route_id"].isin(flex_ids), "trip_id"]
)

trips["weekly_runs"] = (
    trips["service_id"]
    .map(service_days)
    .fillna(0)
    .astype("int8")
)

# Determine active weekdays for each service
week_days = week.drop_duplicates(["service_id", "date"]).copy()

week_days["day_bit"] = (
    pd.to_datetime(week_days["date"], format="%Y%m%d")
    .dt.weekday
    .map(lambda day: 1 << day)
)

service_day_masks = week_days.groupby("service_id")["day_bit"].sum()

trips["day_mask"] = (
    trips["service_id"]
    .map(service_day_masks)
    .fillna(0)
    .astype(int)
)

# Exclude flex services
trips.loc[
    trips["route_id"].isin(flex_ids),
    "weekly_runs"
] = 0

trip_weights = trips.set_index("trip_id")["weekly_runs"]

# Active weekdays for each trip
trip_day_masks = trips.set_index("trip_id")["day_mask"]

# Store on-demand availability per stop
demand_masks = {}

# 5. COUNT DEPARTURES PER STOP
stop_counts = Counter()

for i, chunk in enumerate(
    pd.read_csv(
        DATA / "stop_times.txt",
        usecols=["trip_id", "stop_id", "pickup_type"],
        dtype=str,
        chunksize=500_000
    ),
    start=1
):
    

    # Keep stops with normal boarding
    # 1 = no boarding
    # 2/3 = boarding requires arrangement

    # Identify on-demand transport
    is_demand = (
        chunk["trip_id"].isin(flex_trip_ids)
        | chunk["pickup_type"].isin(["2", "3"])
    )

    # Exclude stops where boarding is not allowed
    can_board = chunk["pickup_type"].fillna("0") != "1"

    demand = chunk.loc[
        is_demand & can_board,
        ["trip_id", "stop_id"]
    ].copy()

    # Find active days for these trips
    demand["day_mask"] = (
        demand["trip_id"]
        .map(trip_day_masks)
        .fillna(0)
        .astype(int)
    )

    demand = demand[demand["day_mask"] > 0]

    # Combine active days per stop
    for stop_id, group in demand.groupby("stop_id"):
        mask = demand_masks.get(stop_id, 0)

        for value in group["day_mask"].unique():
            mask |= int(value)

        demand_masks[stop_id] = mask

    chunk = chunk[
        chunk["pickup_type"].fillna("0") == "0"
    ].copy()

    # Number of departures during the week
    chunk["weekly_runs"] = (
        chunk["trip_id"]
        .map(trip_weights)
        .fillna(0)
        .astype("int8")
    )

    # Keep active departures
    chunk = chunk[chunk["weekly_runs"] > 0]

    # Sum departures per stop
    counts = chunk.groupby("stop_id")["weekly_runs"].sum()

    stop_counts.update(counts.to_dict())

    if i % 5 == 0:
        print(f"Processed {i * 500_000:,} rows")

    # Add on-demand transport: maximum once per active day
    for stop_id, mask in demand_masks.items():
        stop_counts[stop_id] += int(mask).bit_count()
        
# 6. CREATE FINAL CSV
result = pd.DataFrame(
    stop_counts.items(),
    columns=["stop_id", "departures_per_week"]
)

result = result.sort_values(
    "departures_per_week",
    ascending=False
)

result.to_csv(
    GENERATED_DATA / "stop_frequencies.csv",
    index=False
)

# 7. RESULTS
print("\nFinished!")
print("Number of stops:", len(result))

print("\nTop 10 busiest stops:")
print(result.head(10).to_string(index=False))
