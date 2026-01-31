import argparse
import os

import stillsuit


def parse_command_line():
    parser = argparse.ArgumentParser(
        prog="stillsuit_merge_and_reduce",
        description="It merges multiple databases into one and clusters events as it does so",
        epilog="I really hope you enjoy this program.",
    )
    parser.add_argument(
        "-s",
        "--config-schema",
        default=None,
        help="config schema yaml file (optional if input databases contain embedded schema)",
    )
    parser.add_argument(
        "-c",
        "--clustering-column",
        help="column to use for clustering: network_snr, far, likelihood",
    )
    parser.add_argument(
        "-w", "--clustering-window", help="clustering window in seconds", type=float
    )
    parser.add_argument(
        "-d",
        "--db-to-insert-into",
        help="the database to insert into. should not exist",
    )
    parser.add_argument("-v", "--verbose", help="be verbose", action="store_true")
    parser.add_argument(
        "--final-round",
        help="Do a final round of clustering to handle time boundaries",
        action="store_true",
    )
    parser.add_argument("--dbs", action="append", nargs="+")
    args = parser.parse_args()

    if os.path.exists(args.db_to_insert_into):
        raise ValueError("output db exists")

    return args


def main():
    args = parse_command_line()

    # If no config provided, load schema from first input database
    config = args.config_schema
    if config is None:
        first_db = args.dbs[0][0]
        if args.verbose:
            print(f"No config provided, loading schema from {first_db}...")
        # Open first db to get schema, then create output db with same schema
        first = stillsuit.StillSuit(dbname=first_db)
        # We need to get the schema YAML from the db to create outdb
        # For now, just use the first db's schema directly
        outdb = stillsuit.StillSuit(dbname=first_db)
        outdb.db = first.db
        outdb.schema = first.schema
    else:
        outdb = stillsuit.StillSuit(config=config)

    for db_sublist in args.dbs:
        for db_path in db_sublist:
            if args.verbose:
                print(f"merging {db_path} into {args.db_to_insert_into}...")
            db = stillsuit.StillSuit(config=config, dbname=db_path)
            outdb += db
            outdb.cluster(
                win_in_sec=args.clustering_window, column=args.clustering_column
            )

    if args.final_round:
        outdb.cluster_final(
            win_in_sec=args.clustering_window, column=args.clustering_column
        )

    outdb.to_file(args.db_to_insert_into)


if __name__ == "__main__":
    main()
