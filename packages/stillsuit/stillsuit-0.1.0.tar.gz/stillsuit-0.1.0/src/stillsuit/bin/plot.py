import argparse
import os

import yaml
from matplotlib import pyplot

import stillsuit


def parse_command_line():
    parser = argparse.ArgumentParser(
        prog="stillsuit-plot",
        description="YAML driven plotter",
        epilog="I really hope you enjoy this program.",
    )
    parser.add_argument(
        "-s", "--config-schema", help="config schema yaml file for the database"
    )
    parser.add_argument("-c", "--config-plot", help="plot config yaml file")
    parser.add_argument("-d", "--db", help="the database to read from")
    parser.add_argument("-v", "--verbose", help="be verbose", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        raise ValueError("db does not exist")

    return args


def main():
    args = parse_command_line()

    db = stillsuit.StillSuit(config=args.config_schema, dbname=args.db)

    events = list(db.get_events())
    with open(args.config_plot) as f:
        config_plot = yaml.safe_load(f)
    cols = {}
    for plot in config_plot["events"]:
        xk, yk = plot["x"], plot["y"]
        xk1, xk2, yk1, yk2 = xk.split(":") + yk.split(":")
        if xk not in cols:
            cols[xk] = [e[xk1][xk2] for e in events]
        if yk not in cols:
            cols[yk] = [e[yk1][yk2] for e in events]
        X = cols[xk]
        Y = cols[yk]
        pyplot.clf()
        pyplot.plot(X, Y)
        pyplot.savefig(plot["saveas"])


if __name__ == "__main__":
    main()
