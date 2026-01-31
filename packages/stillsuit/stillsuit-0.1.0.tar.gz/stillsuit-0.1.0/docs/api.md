# API Reference

## StillSuit Class

::: stillsuit.StillSuit
    options:
      show_source: true
      members:
        - __post_init__
        - connect
        - load_schema_from_config
        - db_schema
        - insert_static
        - insert_event
        - get_events
        - get_missed_found
        - cluster
        - cluster_final
        - index
        - flush
        - to_file
        - static_tables_and_columns

## Helper Functions

::: stillsuit.serialize

::: stillsuit.deserialize

::: stillsuit.select_data_from_db

::: stillsuit.insert_ignore

## Command-Line Tools

### stillsuit-merge-reduce

Merge multiple databases and cluster events.

```bash
stillsuit-merge-reduce [OPTIONS]
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `-s, --config-schema` | PATH | YAML schema file for database structure (required) |
| `-c, --clustering-column` | TEXT | Column to maximize during clustering (required) |
| `-w, --clustering-window` | FLOAT | Time window in seconds for clustering (required) |
| `-d, --db-to-insert-into` | PATH | Output database path (must not exist) (required) |
| `--dbs` | PATH... | Input database files to merge |
| `--final-round` | FLAG | Apply final clustering round for boundary handling |
| `-v, --verbose` | FLAG | Enable verbose output |

**Example:**

```bash
stillsuit-merge-reduce \
    --config-schema config/tutorial_schema.yaml \
    --clustering-column network_snr \
    --clustering-window 1.0 \
    --db-to-insert-into output.sqlite \
    --verbose \
    --final-round \
    --dbs input1.sqlite input2.sqlite
```

## Schema Configuration

### YAML Schema Format

Each table in the schema is defined with the following structure:

```yaml
table_name:
  columns:
    - {name: "column_name", type: TYPE, constraints: "CONSTRAINTS"}
  relationships:
    - {"foreign_table": "foreign_key_column"}
  static: True/False
  indices:  # optional
    index_name: ["column1", "column2"]
```

### Supported Data Types

| Type | Description |
|------|-------------|
| `NULL` | NULL value |
| `INTEGER` | Signed integer (0-8 bytes) |
| `REAL` | 8-byte IEEE floating point |
| `TEXT` | UTF-8 text string |
| `BLOB` | Binary data |

### Reserved Column Names

Column names starting with `__` or `_` are reserved:

| Column | Description |
|--------|-------------|
| `__filter_id` | Filter/template identifier |
| `__trigger_id` | Trigger unique identifier |
| `__event_id` | Event unique identifier |
| `__data_id` | Data source identifier |
| `__trigger_map_id` | Trigger-event relationship identifier |
| `_simulation_id` | Simulation identifier |

### Required Tables

The following tables must always be defined:

- `trigger` - Individual detector measurements
- `event` - Gravitational wave event candidates

### Automatic Tables

- `trigger_map` - Automatically manages trigger-to-event relationships

## NumPy Type Support

Stillsuit automatically handles NumPy data types:

- `np.int32` / `np.int64` → `INTEGER`
- `np.float16` / `np.float32` / `np.float64` → `REAL`
