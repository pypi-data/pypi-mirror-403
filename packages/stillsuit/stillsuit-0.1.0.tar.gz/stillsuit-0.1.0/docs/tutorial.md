# Tutorial

This tutorial walks through the complete workflow of using Stillsuit for gravitational wave analysis database management.

## Understanding the Data Model

Stillsuit organizes gravitational wave search results into a relational database with the following structure:

```
 --------     ------------
| filter |   | simulation |
 --------     ------------
     |              |         static tables (defined up front)
----------------------------------------------------------------------
     |              |         dynamic tables (appended during analysis)
     v              v
 ---------       -------
| trigger |     | event |
 ---------       -------
        \       |
         \      V
    ===============
   || trigger_map || (automatically generated)
    ===============
```

- **Static tables** (`filter`, `simulation`) contain data defined before the analysis starts
- **Dynamic tables** (`trigger`, `event`) are populated as the analysis progresses
- **trigger_map** is automatically created to relate triggers to events

## Step 1: Define Your Schema

Create a YAML configuration file that defines your database schema. This tutorial uses `config/tutorial_schema.yaml` which is included with stillsuit. You can view it as a reference for creating your own schemas.

The schema defines tables with columns, relationships, and whether they are static (populated once at the start) or dynamic (appended during analysis).

### Schema Rules

1. **Required tables**: `trigger` and `event` must always exist
2. **Reserved columns**: Column names starting with `__` are reserved (e.g., `__filter_id`, `__event_id`)
3. **Supported types**: `NULL`, `INTEGER`, `REAL`, `TEXT`, `BLOB`
4. **Static flag**: Set `static: True` for tables populated before analysis begins

## Step 2: Create a Database and Insert Static Data

```python
import stillsuit

# Create a new database using the tutorial schema
db = stillsuit.StillSuit(config="config/tutorial_schema.yaml")

# Insert filter templates (static data)
filters = []
for i in range(100):
    filters.append({
        "__filter_id": i,
        "mass1": 1.0 + i * 0.1,
        "mass2": 1.0 + i * 0.05,
        "chi": 0.0,
        "approximant": "TaylorF2"
    })

db.insert_static({"filter": filters})

# Insert simulations if doing injection studies
# Times are in nanoseconds (GPS seconds * 1e9)
simulations = []
for i in range(10):
    simulations.append({
        "_simulation_id": i,
        "geocent_end_time": (1000000000 + i * 100) * int(1e9),
        "ra": 1.5,
        "dec": 0.5,
        "distance": 100.0 + i * 50
    })

db.insert_static({"simulation": simulations})

# Commit the static data
db.flush()
```

## Step 3: Insert Events During Analysis

As your analysis pipeline runs, insert events with their associated triggers. First, insert data entries describing each detector's data segment:

```python
# Insert data entries for each detector
data_entries = [
    {"__data_id": 1, "ifo": "H1", "horizon": 120.0},
    {"__data_id": 2, "ifo": "L1", "horizon": 115.0},
]
db.insert_static({"data": data_entries})
```

Then insert events with their triggers. Some events will match simulation times (injections), others won't (background):

```python
# Insert events - some matching simulations, some background
# Times are in nanoseconds (GPS seconds * 1e9)
events_to_insert = [
    # Events matching simulations (found injections)
    {"time": (1000000000 + 100) * int(1e9), "snr": 12.0, "far": 1e-10},  # Matches simulation i=1
    {"time": (1000000000 + 300) * int(1e9), "snr": 9.5, "far": 1e-9},    # Matches simulation i=3
    {"time": (1000000000 + 500) * int(1e9), "snr": 8.2, "far": 1e-8},    # Matches simulation i=5
    {"time": (1000000000 + 700) * int(1e9), "snr": 15.0, "far": 1e-12},  # Matches simulation i=7
    # Background events (no matching simulation)
    {"time": (1000000000 + 50) * int(1e9), "snr": 7.5, "far": 1e-4},
    {"time": (1000000000 + 250) * int(1e9), "snr": 6.8, "far": 1e-3},
    {"time": (1000000000 + 450) * int(1e9), "snr": 8.0, "far": 1e-5},
    {"time": (1000000000 + 650) * int(1e9), "snr": 7.0, "far": 1e-2},
]

for evt in events_to_insert:
    event_data = {
        "trigger": [
            {
                "__filter_id": 42,
                "__data_id": 1,
                "time": evt["time"],
                "snr": evt["snr"] * 0.7,
                "chisq": 1.2,
                "phase": 0.5
            },
            {
                "__filter_id": 42,
                "__data_id": 2,
                "time": evt["time"],
                "snr": evt["snr"] * 0.7,
                "chisq": 1.1,
                "phase": 0.6
            },
        ],
        "event": {
            "time": evt["time"],
            "network_snr": evt["snr"],
            "likelihood": 0.9,
            "far": evt["far"]
        }
    }
    db.insert_event(event_data)
```

!!! note
    The `insert_event` method automatically creates entries in the `trigger_map` table to relate triggers to their parent event.

### Automatic Simulation Matching

If you have a `simulation` table in your schema, `insert_event` will automatically match events to simulations based on time proximity (within 1 second of `geocent_end_time`). To disable this behavior, or if your schema does not include a simulation table, use:

```python
db.insert_event(event_data, ignore_sim=True)
```

!!! warning
    If your schema does not define a `simulation` table, you **must** pass `ignore_sim=True` to `insert_event`, otherwise you will get a `sqlite3.OperationalError: no such table: simulation` error.

## Step 4: Retrieve Events

Use the `get_events` generator to iterate over all events:

```python
for event in db.get_events():
    print(f"Event ID: {event['event']['__event_id']}")
    print(f"Network SNR: {event['event']['network_snr']}")
    print(f"Number of triggers: {len(event['trigger'])}")
    for trig in event['trigger']:
        print(f"  Trigger SNR: {trig['snr']}, Filter ID: {trig['__filter_id']}")
```

### Filter Automatic Columns

To exclude internal columns (those starting with `__`) from the output:

```python
for event in db.get_events(ignore_automatic=True):
    print(event)  # No __event_id, __trigger_id, etc.
```

### Get Events with Simulations

To only retrieve events that matched a simulation:

```python
for event in db.get_events(simulation=True):
    print(f"Injection found at distance: {event['simulation']['distance']}")
```

## Step 5: Analyze Missed and Found Injections

For injection studies, retrieve missed and found simulations:

```python
# Define a selection function (e.g., FAR threshold)
def selection(event):
    return event['event']['far'] < 1e-7

missed, found = db.get_missed_found(selection_func=selection)

print(f"Found {len(found)} injections")
print(f"Missed {len(missed)} injections")

# Analyze missed injections
for m in missed:
    print(f"Missed injection at distance: {m['simulation']['distance']}")
```

## Step 6: Cluster Events

Clustering removes duplicate candidates, keeping only the most significant event within each time window:

```python
# Cluster by network_snr within 1-second windows
db.cluster(win_in_sec=1.0, column="network_snr")

# For finer clustering, use a smaller window
db.cluster(win_in_sec=0.1, column="network_snr")

# Final pass to handle time boundary effects
db.cluster_final(win_in_sec=1.0, column="network_snr")
```

The clustering algorithm:

1. Divides events into time bins of width `win_in_sec`
2. Keeps only the event with maximum `column` value in each bin
3. Removes associated triggers and trigger_map entries for deleted events

## Step 7: Save the Database

```python
# Save to SQLite file
db.to_file("results.sqlite")

# Save compressed (gzip)
db.to_file("results.sqlite.gz")
```

## Complete Example

Here's a complete example combining Steps 2-7 into a single runnable script:

```python
#!/usr/bin/env python3
import stillsuit

# =============================================================================
# Step 2: Create a Database and Insert Static Data
# =============================================================================

# Create a new database using the tutorial schema
db = stillsuit.StillSuit(config="config/tutorial_schema.yaml")

# Insert filter templates (static data)
filters = []
for i in range(100):
    filters.append({
        "__filter_id": i,
        "mass1": 1.0 + i * 0.1,
        "mass2": 1.0 + i * 0.05,
        "chi": 0.0,
        "approximant": "TaylorF2"
    })

db.insert_static({"filter": filters})

# Insert simulations if doing injection studies
# Times are in nanoseconds (GPS seconds * 1e9)
simulations = []
for i in range(10):
    simulations.append({
        "_simulation_id": i,
        "geocent_end_time": (1000000000 + i * 100) * int(1e9),
        "ra": 1.5,
        "dec": 0.5,
        "distance": 100.0 + i * 50
    })

db.insert_static({"simulation": simulations})

# Commit the static data
db.flush()

# =============================================================================
# Step 3: Insert Events During Analysis
# =============================================================================

# First, insert data entries for each detector's data segment
data_entries = [
    {"__data_id": 1, "ifo": "H1", "horizon": 120.0},
    {"__data_id": 2, "ifo": "L1", "horizon": 115.0},
]
db.insert_static({"data": data_entries})

# Insert events - some matching simulations, some background
# Times are in nanoseconds (GPS seconds * 1e9)
events_to_insert = [
    # Events matching simulations (found injections)
    {"time": (1000000000 + 100) * int(1e9), "snr": 12.0, "far": 1e-10},  # Matches simulation i=1
    {"time": (1000000000 + 300) * int(1e9), "snr": 9.5, "far": 1e-9},    # Matches simulation i=3
    {"time": (1000000000 + 500) * int(1e9), "snr": 8.2, "far": 1e-8},    # Matches simulation i=5
    {"time": (1000000000 + 700) * int(1e9), "snr": 15.0, "far": 1e-12},  # Matches simulation i=7
    # Background events (no matching simulation)
    {"time": (1000000000 + 50) * int(1e9), "snr": 7.5, "far": 1e-4},
    {"time": (1000000000 + 250) * int(1e9), "snr": 6.8, "far": 1e-3},
    {"time": (1000000000 + 450) * int(1e9), "snr": 8.0, "far": 1e-5},
    {"time": (1000000000 + 650) * int(1e9), "snr": 7.0, "far": 1e-2},
]

for evt in events_to_insert:
    event_data = {
        "trigger": [
            {
                "__filter_id": 42,
                "__data_id": 1,
                "time": evt["time"],
                "snr": evt["snr"] * 0.7,
                "chisq": 1.2,
                "phase": 0.5
            },
            {
                "__filter_id": 42,
                "__data_id": 2,
                "time": evt["time"],
                "snr": evt["snr"] * 0.7,
                "chisq": 1.1,
                "phase": 0.6
            },
        ],
        "event": {
            "time": evt["time"],
            "network_snr": evt["snr"],
            "likelihood": 0.9,
            "far": evt["far"]
        }
    }
    db.insert_event(event_data)

# =============================================================================
# Step 4: Retrieve Events
# =============================================================================

for event in db.get_events():
    print(f"Event ID: {event['event']['__event_id']}")
    print(f"Network SNR: {event['event']['network_snr']}")
    print(f"Number of triggers: {len(event['trigger'])}")
    for trig in event['trigger']:
        print(f"  Trigger SNR: {trig['snr']}, Filter ID: {trig['__filter_id']}")

# =============================================================================
# Step 5: Analyze Missed and Found Injections
# =============================================================================

# Define a selection function (e.g., FAR threshold)
def selection(event):
    return event['event']['far'] < 1e-7

missed, found = db.get_missed_found(selection_func=selection)

print(f"Found {len(found)} injections")
print(f"Missed {len(missed)} injections")

# Analyze missed injections
for m in missed:
    print(f"Missed injection at distance: {m['simulation']['distance']}")

# =============================================================================
# Step 6: Cluster Events
# =============================================================================

# Cluster by network_snr within 1-second windows
db.cluster(win_in_sec=1.0, column="network_snr")

# =============================================================================
# Step 7: Save the Database
# =============================================================================

# Save to SQLite file
db.to_file("results.sqlite")
```

## Working with Existing Databases

You can open an existing database and perform all the same operations - querying events, analyzing injections, clustering, and more.

```python
import stillsuit

# Open an existing database
db = stillsuit.StillSuit(config="config/tutorial_schema.yaml", dbname="results.sqlite")

# Count total events
event_count = sum(1 for _ in db.get_events())
print(f"Total events: {event_count}")

# Print summary of each event
for event in db.get_events():
    e = event['event']
    print(f"Event {e['__event_id']}: SNR={e['network_snr']:.2f}, FAR={e['far']:.2e}")

# Get events that matched simulations
for event in db.get_events(simulation=True):
    sim = event['simulation']
    e = event['event']
    print(f"Found injection at distance {sim['distance']:.1f} Mpc with SNR {e['network_snr']:.2f}")

# Analyze missed/found injections with a FAR threshold
missed, found = db.get_missed_found(selection_func=lambda x: x['event']['far'] < 1e-7)
print(f"Detection efficiency: {len(found)}/{len(found)+len(missed)} = {len(found)/(len(found)+len(missed))*100:.1f}%")

# You can still cluster or modify the database
db.cluster(win_in_sec=0.5, column="network_snr")

# Save changes to a new file
db.to_file("results_reclustered.sqlite")
```

## Merging Multiple Databases

Combine results from parallel analysis jobs:

```python
# Load the first database
db1 = stillsuit.StillSuit(config="config/tutorial_schema.yaml", dbname="job1.sqlite")

# Load and merge additional databases
db2 = stillsuit.StillSuit(config="config/tutorial_schema.yaml", dbname="job2.sqlite")
db1 += db2

# Cluster after merging
db1.cluster(win_in_sec=1.0, column="network_snr")

# Save merged result
db1.to_file("merged.sqlite")
```

## Using the Command-Line Tool

For production workflows, use `stillsuit-merge-reduce`:

```bash
# First stage: merge and cluster by SNR
stillsuit-merge-reduce \
    --config-schema config/tutorial_schema.yaml \
    --clustering-column network_snr \
    --clustering-window 0.1 \
    --db-to-insert-into stage1.sqlite \
    --verbose \
    --dbs job1.sqlite job2.sqlite job3.sqlite

# Second stage: cluster by likelihood with larger window
stillsuit-merge-reduce \
    --config-schema config/tutorial_schema.yaml \
    --clustering-column likelihood \
    --clustering-window 4.0 \
    --db-to-insert-into stage2.sqlite \
    --verbose \
    --final-round \
    --dbs stage1.sqlite
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `-s, --config-schema` | YAML schema file |
| `-c, --clustering-column` | Column to maximize during clustering |
| `-w, --clustering-window` | Time window in seconds |
| `-d, --db-to-insert-into` | Output database path (must not exist) |
| `--dbs` | Input database files |
| `--final-round` | Apply final clustering pass |
| `-v, --verbose` | Verbose output |

## Working with In-Place Databases

For large databases that don't fit in memory, use `inplace=True`:

```python
# Work directly on the file (not in memory)
db = stillsuit.StillSuit(
    config="config/tutorial_schema.yaml",
    dbname="large_db.sqlite",
    inplace=True
)

# Modifications are made directly to the file
db.cluster(win_in_sec=1.0, column="network_snr")
db.flush()
```

!!! warning
    In-place mode is not compatible with gzip-compressed databases or `:memory:` databases.

## Context Manager Usage

Use the context manager pattern to ensure proper cleanup:

```python
with stillsuit.StillSuit(config="config/tutorial_schema.yaml") as db:
    # Insert data...
    db.insert_static({"filter": [...]})

    # Process events...
    for event in some_pipeline():
        db.insert_event(event)

    # Save results
    db.to_file("output.sqlite")
# Database is automatically committed on exit
```
