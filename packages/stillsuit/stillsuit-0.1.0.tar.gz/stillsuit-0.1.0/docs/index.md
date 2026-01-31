# Stillsuit

<p align="center">
  <img src="assets/logo.png" alt="Stillsuit Logo" width="180">
</p>

A Python package for managing gravitational wave detection analysis results using SQLite databases.

## Overview

Stillsuit provides an interface to SQLite databases that facilitates the storage and analysis of gravitational wave (GW) search results, particularly for CBC (Compact Binary Coalescence) searches. It manages relationships between:

- **Filters** - Template parameters (e.g., CBC template masses, spins)
- **Triggers** - Individual detector measurements
- **Events** - Gravitational wave candidates (collections of triggers)
- **Simulations** - Injected signals for sensitivity studies

## Installation

```bash
pip install stillsuit
```

Or install from source:

```bash
git clone https://git.ligo.org/greg/stillsuit
cd stillsuit
pip install .
```

### Documentation Dependencies

To build the documentation locally:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
mkdocs serve
```

## Quick Start

```python
import stillsuit

# Create a new in-memory database with your schema
with stillsuit.StillSuit(config="config/tutorial_schema.yaml") as db:
    # Insert static data (templates)
    db.insert_static({
        "filter": [
            {"__filter_id": 1, "mass1": 1.4, "mass2": 1.4, "chi": 0.0},
            {"__filter_id": 2, "mass1": 2.0, "mass2": 1.5, "chi": 0.1},
        ]
    })

    # Insert an event with triggers
    db.insert_event({
        "trigger": [
            {"__filter_id": 1, "snr": 8.5, "time": 1000000000},
            {"__filter_id": 1, "snr": 7.2, "time": 1000000001},
        ],
        "event": {
            "time": 1000000000,
            "network_snr": 11.1,
            "likelihood": 0.95,
        }
    })

    # Retrieve events
    for event in db.get_events():
        print(event)

    # Save to file
    db.to_file("output.sqlite")
```

## Command-Line Tools

Stillsuit provides the `stillsuit-merge-reduce` command for merging databases and clustering events:

```bash
stillsuit-merge-reduce \
    --config-schema config/tutorial_schema.yaml \
    --clustering-column network_snr \
    --clustering-window 1.0 \
    --db-to-insert-into output.sqlite \
    --dbs input1.sqlite input2.sqlite
```

## License

Mozilla Public License 2.0 (MPL 2.0)
