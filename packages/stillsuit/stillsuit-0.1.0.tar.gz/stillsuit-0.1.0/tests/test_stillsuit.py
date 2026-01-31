#!/usr/bin/env python3
import pprint
import random

import stillsuit


def test_stillsuit_fake_cbc():
    random.seed(10191)
    out = fakedb(config="config/fake_cbc.yaml")
    # Verify structure - event with triggers
    assert "event" in out
    assert "trigger" in out
    assert "__event_id" in out["event"]
    assert len(out["trigger"]) == 3
    for t in out["trigger"]:
        assert "__trigger_id" in t
        assert "__filter_id" in t


def test_stillsuit_fake():
    random.seed(10191)
    out = fakedb(config="config/fake.yaml")
    # Verify structure - event with triggers
    assert "event" in out
    assert "trigger" in out
    assert "__event_id" in out["event"]
    assert len(out["trigger"]) == 3
    for t in out["trigger"]:
        assert "__trigger_id" in t
        assert "__filter_id" in t


def fake_value(c):
    if c["type"] == "REAL":
        return random.random()
    if c["type"] == "TEXT":
        return "blah"
    if c["type"] == "INTEGER":
        return random.randint(0, 10)


def fake_row(table, extra={}):
    out = {
        c["name"]: fake_value(c)
        for c in table["columns"]
        if not c["name"].startswith("__")
    }
    out.update(extra)
    return out


# def fakedb(config = "config/fake.yaml", dbname = ":memory:"):
def fakedb(config="config/fake_cbc.yaml", dbname=":memory:"):

    with stillsuit.StillSuit(config=config, dbname=dbname) as out:
        # Insert 100 fake filters, e.g., cbc templates
        for _ in range(100):
            out.insert_static({"filter": [fake_row(out.schema["filter"])]})

        # Insert 200 fake simulations, e.g,. cbc waveform parameter rows
        # for n in range(200):
        #   out.insert_static({"simulation": fake_row(out.schema['simulation'])})

        # get filter and simulation ids
        filter_ids = out.default_cursor.execute(
            "SELECT __filter_id FROM filter;"
        ).fetchall()
        # simulation_ids = out.default_cursor.execute("SELECT __simulation_id FROM simulation;").fetchall()

        # Insert 1,000 fake events, e.g., the results of a CBC search
        for _ in range(1):
            out.insert_event(
                {
                    "trigger": [
                        fake_row(
                            out.schema["trigger"],
                            extra={"__filter_id": random.choices(filter_ids)[0][0]},
                        )
                        for x in range(3)
                    ],
                    "event": fake_row(out.schema["event"]),
                },
                ignore_sim=True,
            )
        # Retreive the events from the DB
        for _, row in enumerate(out.get_events()):
            pprint.pp(row)

        return row


if __name__ == "__main__":
    # "loading a nonsense fake schema"
    # test_stillsuit_fake()
    "loading a stripped down CBC search schema"
    test_stillsuit_fake_cbc()
