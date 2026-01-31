import argparse
import sys

import stillsuit


def parse_command_line():
    parser = argparse.ArgumentParser(
        prog="stillsuit_show",
        description="Display contents of a stillsuit database with joined data",
        epilog="Inspect your gravitational wave search results.",
    )
    parser.add_argument(
        "-s",
        "--config-schema",
        default=None,
        help="config schema yaml file (optional if database contains embedded schema)",
    )
    parser.add_argument("-d", "--db", required=True, help="database file to read")
    parser.add_argument(
        "--columns",
        nargs="+",
        default=None,
        help="specific columns to display (default: all visible)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="show all columns including those with display: None in schema",
    )
    parser.add_argument("--no-header", action="store_true", help="suppress header row")
    parser.add_argument(
        "--delimiter", default="\t", help="column delimiter (default: tab)"
    )
    parser.add_argument(
        "--injections-only",
        action="store_true",
        help="only show events that matched simulations",
    )
    parser.add_argument(
        "--missed", action="store_true", help="show missed injections instead of events"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="show summary statistics instead of event table",
    )
    args = parser.parse_args()
    return args


def get_hidden_columns(schema):
    """
    Get set of column names that have display: false/None in the schema.
    Returns prefixed column names like 'event_time', 'trigger_snr', etc.
    """
    hidden = set()
    prefix_map = {
        "event": "event",
        "trigger": "trigger",
        "filter": "filter",
        "data": "data",
        "simulation": "sim",
    }
    for table, prefix in prefix_map.items():
        if table in schema:
            for col in schema[table].get("columns", []):
                # Check if display is explicitly set to a falsy value (None, False, false)
                if "display" in col and not col.get("display"):
                    name = col["name"].lstrip("_")
                    hidden.add(f"{prefix}_{name}")
    return hidden


def get_flat_events(db, injections_only=False):
    """
    Generator that yields flattened event dictionaries with all joined data.
    Each trigger becomes its own row with event, filter, and data info joined.
    """
    for event in db.get_events(simulation=injections_only):
        event_data = event["event"]
        simulation_data = event.get("simulation", {})

        for trigger in event["trigger"]:
            row = {}

            # Add event columns (prefix with event_)
            for k, v in event_data.items():
                if not k.startswith("__"):
                    row[f"event_{k}"] = v

            # Add trigger columns (prefix with trigger_)
            for k, v in trigger.items():
                if not k.startswith("__"):
                    row[f"trigger_{k}"] = v

            # Look up filter data if we have filter_id
            filter_id = trigger.get("__filter_id")
            if filter_id is not None:
                filter_row = (
                    db.db.cursor()
                    .execute("SELECT * FROM filter WHERE __filter_id = ?", (filter_id,))
                    .fetchone()
                )
                if filter_row:
                    for k, v in dict(filter_row).items():
                        if not k.startswith("__"):
                            row[f"filter_{k}"] = v

            # Look up data info if we have data_id
            data_id = trigger.get("__data_id")
            if data_id is not None:
                try:
                    data_row = (
                        db.db.cursor()
                        .execute("SELECT * FROM data WHERE __data_id = ?", (data_id,))
                        .fetchone()
                    )
                    if data_row:
                        for k, v in dict(data_row).items():
                            if not k.startswith("__"):
                                row[f"data_{k}"] = v
                except Exception:
                    pass  # data table may not exist

            # Add simulation data if present
            if simulation_data:
                for k, v in simulation_data.items():
                    if not k.startswith("_"):
                        row[f"sim_{k}"] = v

            yield row


def get_missed_injections(db):
    """
    Generator that yields flattened missed injection dictionaries.
    """
    missed, _ = db.get_missed_found()
    for m in missed:
        row = {}
        for k, v in m["simulation"].items():
            if not k.startswith("_"):
                row[f"sim_{k}"] = v
        yield row


def format_value(v):
    """Format a value for display."""
    if v is None:
        return ""
    if isinstance(v, float):
        # Use scientific notation for very small/large numbers, otherwise reasonable precision
        if v != 0 and (abs(v) < 1e-4 or abs(v) >= 1e8):
            return f"{v:.3e}"
        else:
            return f"{v:.6g}"
    return str(v)


def print_table(
    rows,
    columns=None,
    hidden_columns=None,
    delimiter="\t",
    header=True,
    file=sys.stdout,
):
    """
    Print rows as a delimited table with aligned columns.
    """
    rows = list(rows)
    if not rows:
        print("No data to display.", file=sys.stderr)
        return

    hidden_columns = hidden_columns or set()

    # Determine columns
    if columns is None:
        # Get all unique columns preserving rough order, excluding hidden ones
        seen = set()
        columns = []
        for row in rows:
            for k in row.keys():
                if k not in seen and k not in hidden_columns:
                    seen.add(k)
                    columns.append(k)

    # Format all values and calculate column widths
    formatted_rows = []
    for row in rows:
        formatted_rows.append([format_value(row.get(col)) for col in columns])

    # Split headers into prefix (event, trigger, filter, data, sim) and remainder
    split_headers = []
    for col in columns:
        parts = col.split("_", 1)  # Split only on first underscore
        if len(parts) == 1:
            split_headers.append(("", parts[0]))
        else:
            # Remove leading underscore from name if present (e.g., _simulation_id -> simulation_id)
            name = parts[1].lstrip("_")
            split_headers.append((parts[0], name))

    # Calculate column widths (considering split headers and data)
    widths = []
    for i, (prefix, name) in enumerate(split_headers):
        max_header_width = max(len(prefix), len(name))
        max_data_width = (
            max(len(row[i]) for row in formatted_rows) if formatted_rows else 0
        )
        widths.append(max(max_header_width, max_data_width))

    # Print header (two lines: prefix and name)
    if header:
        prefix_parts = [
            split_headers[i][0].ljust(widths[i]) for i in range(len(columns))
        ]
        name_parts = [split_headers[i][1].ljust(widths[i]) for i in range(len(columns))]
        print(delimiter.join(prefix_parts), file=file)
        print(delimiter.join(name_parts), file=file)

    # Print rows
    for row in formatted_rows:
        row_parts = [val.ljust(widths[i]) for i, val in enumerate(row)]
        print(delimiter.join(row_parts), file=file)


def print_summary(db):
    """Print summary statistics."""
    print("=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)

    # Count events
    event_count = sum(1 for _ in db.get_events())
    print(f"Total events: {event_count}")

    # Count events with simulations
    sim_event_count = sum(1 for _ in db.get_events(simulation=True))
    print(f"Events matched to simulations: {sim_event_count}")

    # Count filters
    filter_count = db.db.cursor().execute("SELECT COUNT(*) FROM filter").fetchone()[0]
    print(f"Filter templates: {filter_count}")

    # Count simulations (if table exists)
    try:
        sim_count = (
            db.db.cursor().execute("SELECT COUNT(*) FROM simulation").fetchone()[0]
        )
        print(f"Simulations: {sim_count}")
        if sim_count > 0:
            missed, found = db.get_missed_found()
            print(f"  Found: {len(found)}")
            print(f"  Missed: {len(missed)}")
    except Exception:
        print("Simulations: N/A (no simulation table)")

    # Count triggers
    trigger_count = db.db.cursor().execute("SELECT COUNT(*) FROM trigger").fetchone()[0]
    print(f"Total triggers: {trigger_count}")

    print()


def main():
    args = parse_command_line()

    db = stillsuit.StillSuit(config=args.config_schema, dbname=args.db)

    # Determine which columns to hide (unless --all is specified)
    if args.all:
        hidden_columns = set()
    else:
        hidden_columns = get_hidden_columns(db.schema)

    if args.summary:
        print_summary(db)
    elif args.missed:
        rows = get_missed_injections(db)
        print_table(
            rows,
            columns=args.columns,
            hidden_columns=hidden_columns,
            delimiter=args.delimiter,
            header=not args.no_header,
        )
    else:
        rows = get_flat_events(db, injections_only=args.injections_only)
        print_table(
            rows,
            columns=args.columns,
            hidden_columns=hidden_columns,
            delimiter=args.delimiter,
            header=not args.no_header,
        )


if __name__ == "__main__":
    main()
