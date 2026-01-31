# Command-Line Tools

Stillsuit provides two command-line tools for working with databases outside of Python.

## stillsuit-show

Display the contents of a stillsuit database with all data joined into a flat table format.

### Basic Usage

```bash
# Display all events with joined trigger, filter, and data information
stillsuit-show -d results.sqlite

# Show summary statistics instead of event table
stillsuit-show -d results.sqlite --summary

# Show only events that matched simulations (injections)
stillsuit-show -d results.sqlite --injections-only

# Show missed injections
stillsuit-show -d results.sqlite --missed
```

### Output Format

By default, `stillsuit-show` outputs a tab-delimited table with two header rows:

1. **Prefix row**: Table prefix (`event`, `trigger`, `filter`, `data`, `sim`)
2. **Name row**: Column name within that table

```
event     event        event       trigger   trigger   filter   filter
time      network_snr  far         snr       chisq     mass1    mass2
1.00e+18  12           1e-10       8.4       1.2       5.1      3.05
1.00e+18  12           1e-10       8.4       1.1       5.1      3.05
```

### Column Selection

```bash
# Show only specific columns
stillsuit-show -d results.sqlite --columns event_network_snr event_far trigger_snr

# Show all columns including hidden ones (display: false in schema)
stillsuit-show -d results.sqlite --all
```

### Formatting Options

```bash
# Use comma as delimiter (for CSV output)
stillsuit-show -d results.sqlite --delimiter ","

# Suppress header rows
stillsuit-show -d results.sqlite --no-header

# Combine for clean CSV export
stillsuit-show -d results.sqlite --delimiter "," --no-header > events.csv
```

### Hidden Columns

Columns marked with `display: false` in the schema are hidden by default. Use `--all` to show them:

```yaml
# In your schema YAML
filter:
  columns:
    - name: mass1
      type: REAL
    - name: internal_id
      type: INTEGER
      display: false  # Hidden by default
```

```bash
# internal_id is hidden
stillsuit-show -d results.sqlite

# internal_id is visible
stillsuit-show -d results.sqlite --all
```

### Summary Mode

Get a quick overview of database contents:

```bash
stillsuit-show -d results.sqlite --summary
```

Output:
```
============================================================
DATABASE SUMMARY
============================================================
Total events: 8
Events matched to simulations: 4
Filter templates: 100
Simulations: 10
  Found: 4
  Missed: 6
Total triggers: 16
```

### Command Reference

| Option | Description |
|--------|-------------|
| `-d, --db` | Database file to read (required) |
| `-s, --config-schema` | Schema YAML file (optional if embedded in database) |
| `--columns` | Specific columns to display |
| `--all` | Show all columns including hidden ones |
| `--no-header` | Suppress header rows |
| `--delimiter` | Column delimiter (default: tab) |
| `--injections-only` | Only show events that matched simulations |
| `--missed` | Show missed injections instead of events |
| `--summary` | Show summary statistics |

---

## stillsuit-merge-reduce

Merge multiple databases into one while clustering events.

### Basic Usage

```bash
stillsuit-merge-reduce \
    --clustering-column network_snr \
    --clustering-window 1.0 \
    --db-to-insert-into merged.sqlite \
    --dbs job1.sqlite job2.sqlite job3.sqlite
```

### Multi-Stage Workflow

For production pipelines, use multiple merge-reduce stages with different clustering parameters:

```bash
# Stage 1: Merge parallel job outputs, cluster by SNR with fine window
stillsuit-merge-reduce \
    --clustering-column network_snr \
    --clustering-window 0.1 \
    --db-to-insert-into stage1.sqlite \
    --verbose \
    --dbs job1.sqlite job2.sqlite job3.sqlite job4.sqlite

# Stage 2: Re-cluster with larger window and different column
stillsuit-merge-reduce \
    --clustering-column likelihood \
    --clustering-window 4.0 \
    --db-to-insert-into stage2.sqlite \
    --verbose \
    --final-round \
    --dbs stage1.sqlite
```

### Final Round Clustering

Use `--final-round` on the last stage to handle events near time bin boundaries:

```bash
stillsuit-merge-reduce \
    --clustering-column network_snr \
    --clustering-window 1.0 \
    --db-to-insert-into final.sqlite \
    --final-round \
    --dbs intermediate.sqlite
```

### Command Reference

| Option | Description |
|--------|-------------|
| `-d, --db-to-insert-into` | Output database path (must not exist) |
| `-c, --clustering-column` | Column to maximize during clustering (`network_snr`, `far`, `likelihood`) |
| `-w, --clustering-window` | Clustering time window in seconds |
| `--dbs` | Input database files to merge |
| `-s, --config-schema` | Schema YAML file (optional if embedded in input databases) |
| `--final-round` | Apply final clustering pass for time boundary handling |
| `-v, --verbose` | Print progress messages |

### Notes

- The output database must not already exist
- If `--config-schema` is not provided, the schema is loaded from the first input database
- Clustering keeps the event with the maximum value of `--clustering-column` in each time window
- Use `--final-round` only on the final merge stage to avoid duplicate processing
