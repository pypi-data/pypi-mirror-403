import gzip
import os
import sqlite3
import tempfile
from dataclasses import dataclass

import numpy as np
import yaml

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0"


# FIXME These methods are implemented to support serialization in old versions of python that don't have the methods
def serialize(conn):
    with tempfile.NamedTemporaryFile() as f:
        conn.execute(f"vacuum main into '{f.name}'")
        return f.read()


def deserialize(conn, byte_stream):
    with tempfile.NamedTemporaryFile() as f:
        f.write(byte_stream)
        f.flush()
        c = sqlite3.connect(f.name)
        c.backup(conn)
        conn.commit()
        c.close()


@dataclass
class StillSuit:
    """
    This class provides an interface to an sqlite database that facilitates the
    storage of gravitational wave results.  It defines methods that are largely
    agnostic about e.g., column names, but some tables must exist and some
    relationships must exist.

       These tables will be related in the following way

        --------     ------------
       | filter |   | simulation |
        --------     ------------
            |              |         static tables (defined up front)
      ------------------------------------------------------------------------------------------------------
            |              |         dynamic tables (appended to as analysis progresses)
            v              v
        ---------       -------
       | trigger |     | event |
        ---------       -------
               \\       |
                \\      V
           ===============
          || trigger map || This table is automatically generated
           ===============

    Users define their own column names in a yaml file called "config" that will be
    provided to this class to initialize it. It is required always since it also
    defines schema validation.

    When starting an analysis from scratch, it is expected that the user will
    first insert some static data in the filter table (e.g., a table defining CBC
    template parameters or burst template parameters) and a simulation table
    (optional) if injections were performed which holds parameters about a
    simulated signal put into the data.

    As an analysis progresses, it is expected that events are inserted one by
    one. Events are actually a relationship between three tables 1) a trigger table
    holding measured parameters of one GW detector search; 2) an event table which
    holds data corresponding to the gravitational wave event defined a the
    collection of one or more triggers.  A third table called "trigger_map" will be
    automatically made by this class to define the relationships.

    NOTE: according to documentation:
    https://www.sqlite.org/lang_createtable.html#rowid, the primary keys defined in
    the schema all follow the convention that they will be an alias for the built
    in rowid.

    Parameters:
    ===========

    config: dict
        A dictionary (just the output of yaml.load) defining the custom user schema
    dbname: str
        The database name. If it exists it will be loaded, if not it will be created.  Default ":memory:"
    inplace:
        Transform the database in place.  Incompatable with in memory databases or gzip database. Default: False
    """

    config: str = None
    dbname: str = ":memory:"
    inplace: bool = False

    REQUIRED_TABLES = set(("trigger", "event"))
    METADATA_TABLE = "_stillsuit_metadata"

    def __post_init__(self):
        """
        Setup the database, row factory and schema
        """
        if self.config is None and self.dbname == ":memory:":
            raise ValueError(
                "config is required when creating a new in-memory database"
            )

        if self.dbname != ":memory:" and not os.path.exists(self.dbname):
            raise ValueError(
                "If providing a dbname that isn't :memory: (the default), the DB must exist.  If you want to produce a new database use :memory: and then write the result to a file with the to_file(...) method"
            )

        if self.inplace and (self.dbname == ":memory:" or self.dbname.endswith(".gz")):
            raise ValueError(
                "inplace is only supported if given an existing database name that is not gzip compressed"
            )
        self.db, self.schema = self.connect(
            self.config, self.dbname, inplace=self.inplace
        )
        self.db.row_factory = sqlite3.Row
        self.default_cursor = self.db.cursor()
        self.index()
        sqlite3.register_adapter(np.int32, lambda val: int(val))
        sqlite3.register_adapter(np.int64, lambda val: int(val))
        sqlite3.register_adapter(np.float16, lambda val: float(val))
        sqlite3.register_adapter(np.float32, lambda val: float(val))
        sqlite3.register_adapter(np.float64, lambda val: float(val))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Make sure the DB is committed if exiting
        """
        self.flush()

    def index(self):
        for k, v in self.schema.items():
            if "indices" in v:
                for name, cols in v["indices"].items():
                    cols = ",".join(cols)
                    self.default_cursor.execute(
                        f"CREATE INDEX IF NOT EXISTS {name} ON {k} ({cols});"
                    )

    def flush(self):
        """
        Commit the DB results. This will generally only be done if asked. An exception is when the initial structure is set up for a new db
        """
        self.db.commit()

    def to_file(self, filename: str):
        """
        Save in-memory database to file
        """
        self.flush()
        if filename.endswith(".gz"):
            with open(filename, "wb") as f:
                # FIXME work around old python versions
                if hasattr(self.db, "serialize"):
                    f.write(gzip.compress(self.db.serialize()))
                else:
                    f.write(gzip.compress(serialize(self.db)))
        else:
            self.db.execute(f"vacuum main into '{filename}'")

    def __insert_dict(self, t, d, cursor=None, extra=None, ignore_cols=None):
        cursor = cursor or self.default_cursor

        if isinstance(d, dict):
            # dictionaries
            columns = tuple(d.keys())
            values = tuple(d.values())
        else:
            # numpy custom dtypes
            columns = d.dtype.names
            values = tuple(d)

        if extra is not None:
            columns += tuple(extra)
            values += tuple(extra.values())

        if ignore_cols:
            values = tuple(v for c, v in zip(columns, values) if c not in ignore_cols)
            columns = tuple(c for c in columns if c not in ignore_cols)

        sql = "INSERT INTO %s(%s) VALUES (%s);" % (
            t,
            ",".join(columns),
            ",".join(["?"] * (len(columns))),
        )
        cursor.execute(sql, values)
        return cursor

    def insert_static(self, d, cursor=None):
        """
        This is a method to insert list of dictionarys of static data, e.g.,

        d = {"filter": [{"col1":<value1>,...}, {"col1":<value2>,...}]}
        """

        cursor = cursor or self.default_cursor
        # FIXME do any sort of sanity checking
        for t, td in d.items():
            for di in td:
                self.__insert_dict(t, di, cursor)

    def insert_event(self, d, ignore_sim=False, ignore_cols=None):
        """
        Required format
        {
         "trigger": [{...}, ...],
         "event": {...}
        }

        Furthermore, data and trigger must have the same length and be 1:1.

        NOTE: this method modifies the trigger and event dictionaries to add
        references to internal keys.  If you don't want that behavior save a copy
        before you insert or otherwise deal with it.
        """
        assert not (set(d) - set(("trigger", "event")))
        if not ignore_sim:
            for inj in self.db.cursor().execute(
                "SELECT _simulation_id FROM simulation WHERE abs(geocent_end_time - %s) < 1e9;"
                % d["event"]["time"]
            ):
                d["event"]["_simulation_id"] = dict(inj)["_simulation_id"]

        ignore_cols_event = None
        ignore_cols_trigger = None
        if ignore_cols:
            if "event" in ignore_cols:
                ignore_cols_event = ignore_cols["event"]
            if "trigger" in ignore_cols:
                ignore_cols_trigger = ignore_cols["trigger"]

        event_id = self.__insert_dict(
            "event", d["event"], ignore_cols=ignore_cols_event
        ).lastrowid
        for r in d["trigger"]:
            if r is not None:
                trigger_id = self.__insert_dict(
                    "trigger", r, ignore_cols=ignore_cols_trigger
                ).lastrowid
                self.__insert_dict(
                    "trigger_map", {"__event_id": event_id, "__trigger_id": trigger_id}
                )

    def get_events(self, ignore_automatic=False, simulation=False):
        """
        A generator to return a dictionary of all the information about an event
        """

        # FIXME
        def del_automatic(d):
            return {k: v for k, v in d.items() if not k.startswith("__")}

        cursor1 = self.db.cursor()
        cursor2 = self.db.cursor()
        cursor3 = self.db.cursor()
        query = (
            "SELECT * FROM event;"
            if not simulation
            else "SELECT * FROM event WHERE _simulation_id IS NOT NULL;"
        )
        for row in cursor1.execute(query):
            out = {"event": dict(row)}
            out["trigger"] = [
                dict(x)
                for x in cursor3.execute(
                    "SELECT * FROM trigger JOIN trigger_map ON trigger.__trigger_id == trigger_map.__trigger_id WHERE trigger_map.__event_id == ?",
                    (out["event"]["__event_id"],),
                )
            ]
            if simulation:
                out["simulation"] = dict(
                    cursor2.execute(
                        "SELECT * FROM simulation WHERE simulation._simulation_id == ?",
                        (out["event"]["_simulation_id"],),
                    ).fetchone()
                )
            if ignore_automatic:
                out["event"] = del_automatic(out["event"])
                out["trigger"] = [del_automatic(x) for x in out["trigger"]]
            yield out

    def get_missed_found(self, selection_func=lambda x: True, ignore_automatic=False):
        found = {
            x["event"]["_simulation_id"]: x
            for x in self.get_events(ignore_automatic=ignore_automatic, simulation=True)
            if selection_func(x)
        }
        missed = [
            {"simulation": dict(row)}
            for row in self.db.cursor().execute("SELECT * FROM simulation")
            if dict(row)["_simulation_id"] not in found
        ]
        return missed, list(found.values())

    @classmethod
    def db_schema(cls, db):
        """
        Return the current schema in the database
        """
        return {
            n: s
            for n, s in db.cursor().execute(
                "SELECT name, sql FROM sqlite_master WHERE type='table';"
            )
        }

    @classmethod
    def load_schema_from_config(cls, config):
        """
        Load the user schema from a config file, then

        1) Validate that the required tables are present
        2) Add a new "trigger_map" table.
        3) Merge the BASE SCHEMA (class defined special column names and relationships) into the user schema

        return the merged schema.

        """
        with open(config) as f:
            user_schema = yaml.safe_load(f)
        return cls._process_schema(user_schema)

    @classmethod
    def _process_schema(cls, user_schema):
        """
        Process and validate a schema dictionary.
        """
        assert not (cls.REQUIRED_TABLES - set(user_schema))
        for t in user_schema:
            for c in user_schema[t]["columns"]:
                if "constraints" not in c:
                    c["constraints"] = ""
        return user_schema

    @classmethod
    def _save_schema_to_db(cls, db, config_path):
        """
        Save the schema YAML to the database metadata table.
        """
        with open(config_path) as f:
            schema_yaml = f.read()
        db.cursor().execute(
            f"CREATE TABLE IF NOT EXISTS {cls.METADATA_TABLE} (key TEXT PRIMARY KEY, value TEXT)"
        )
        db.cursor().execute(
            f"INSERT OR REPLACE INTO {cls.METADATA_TABLE} (key, value) VALUES (?, ?)",
            ("schema_yaml", schema_yaml),
        )
        db.commit()

    @classmethod
    def _load_schema_from_db(cls, db):
        """
        Load the schema from the database metadata table.
        Returns the schema dict or None if not found.
        """
        try:
            result = (
                db.cursor()
                .execute(
                    f"SELECT value FROM {cls.METADATA_TABLE} WHERE key = ?",
                    ("schema_yaml",),
                )
                .fetchone()
            )
            if result:
                user_schema = yaml.safe_load(result[0])
                return cls._process_schema(user_schema)
        except sqlite3.OperationalError:
            pass
        return None

    @classmethod
    def connect(cls, config, dbname, inplace=False):
        """
        This class method allows a user to connect to an sqlite database.  In
        some ways, it is similar to the sqlite3.connect() function, but it adds schema
        validation and initializes an empty database.  It also returns the schema
        dictionary that was applied to the DB.

        If config is None and dbname points to an existing database, the schema
        will be loaded from the database's metadata table.
        """

        def init_tables(__schema, __db):
            def column(c):
                return "%s %s %s" % (c["name"], c["type"], c["constraints"])

            def foreign_keys(table, relationships):
                x = [
                    "FOREIGN KEY (%s) REFERENCES %s(%s)" % (c, t, c)
                    for d in relationships
                    for t, c in d.items()
                ]
                return x

            for t in __schema:
                fs = [column(c) for c in __schema[t]["columns"]]
                fs += foreign_keys(t, __schema[t]["relationships"])
                q = "CREATE TABLE IF NOT EXISTS %s (%s)" % (t, ", ".join(fs))
                __db.cursor().execute(q)

            __db.commit()

        def new_db(_schema, _config_path=None):
            _db = sqlite3.connect(":memory:")
            init_tables(_schema, _db)
            # Save schema to metadata table if we have the config path
            if _config_path:
                cls._save_schema_to_db(_db, _config_path)
            return _db, _schema

        # If no config provided, try to load from existing database
        if config is None:
            if dbname.endswith(".gz"):
                with gzip.open(dbname, "rb") as f:
                    bites = f.read()
                db = sqlite3.connect(":memory:")
                if hasattr(db, "deserialize"):
                    db.deserialize(bites)
                else:
                    deserialize(db, bites)
            else:
                db = sqlite3.connect(dbname)

            schema = cls._load_schema_from_db(db)
            if schema is None:
                db.close()
                raise ValueError(
                    "No config provided and database does not contain embedded schema. "
                    "Please provide a config file or use a database created with a newer version of stillsuit."
                )

            if not inplace:
                db_mem = sqlite3.connect(":memory:")
                db.backup(db_mem)
                db.close()
                return db_mem, schema
            else:
                return db, schema

        # Config provided - load schema from file
        schema = cls.load_schema_from_config(config)

        db_ref, _ = new_db(schema, config)
        if dbname.endswith(".gz"):
            with gzip.open(dbname, "rb") as f:
                bites = f.read()
            db = sqlite3.connect(":memory:")
            # FIXME work around old python versions
            if hasattr(db, "deserialize"):
                db.deserialize(bites)
            else:
                deserialize(db, bites)
        elif dbname == ":memory:":
            return db_ref, schema
        else:
            db = sqlite3.connect(dbname)

        # Compare schemas (excluding metadata table)
        db_ref_schema = {
            k: v for k, v in cls.db_schema(db_ref).items() if k != cls.METADATA_TABLE
        }
        db_schema = {
            k: v for k, v in cls.db_schema(db).items() if k != cls.METADATA_TABLE
        }

        if db_ref_schema == db_schema:
            if not inplace:
                db.backup(db_ref)
                db.close()
                return db_ref, schema
            else:
                db_ref.close()
                # Save schema to existing db if not already there
                if cls._load_schema_from_db(db) is None:
                    cls._save_schema_to_db(db, config)
                return db, schema
        else:
            db_ref.close()
            db.close()
            raise ValueError("Database schema does not match")

    @property
    def static_tables_and_columns(self):
        return {
            t: [c["name"] for c in v["columns"]]
            for t, v in self.schema.items()
            if v["static"]
        }

    def __iadd__(self, other):
        for table_name, column_names in self.static_tables_and_columns.items():
            rows = select_data_from_db(other.db.cursor(), table_name)
            insert_ignore(self.db.cursor(), table_name, rows, column_names)
        for event in other.get_events(ignore_automatic=True):
            # injection assignment will not be done on the fly here because it
            # is slow. Since injection ids are supposed to be global, this is
            # fine. And if this isn't fine, you have bigger problems
            self.insert_event(event, ignore_sim=True)
        self.db.commit()
        return self

    def cluster(self, win_in_sec=1.0, column="network_snr"):
        """
        Cluster the current database by events that maximize "column" within a fixed time window of "win_in_sec"
        """
        # Actually does the clustering
        self.db.cursor().execute(
            f"CREATE TEMPORARY TABLE event_ids_to_save AS SELECT __event_id, cast(time*1e-9/{win_in_sec} as int) AS tid, max({column}) FROM event GROUP BY tid;"
        )

        # Delets all the stuff that doesn't survive clustering
        self.db.cursor().execute(
            "CREATE TEMPORARY TABLE trigger_ids_to_delete AS SELECT __trigger_id FROM trigger_map WHERE __event_id NOT IN (SELECT __event_id FROM event_ids_to_save)"
        )
        self.db.cursor().execute(
            "DELETE FROM event WHERE __event_id NOT IN (SELECT __event_id FROM event_ids_to_save)"
        )
        self.db.cursor().execute(
            "DELETE FROM trigger WHERE __trigger_id IN (SELECT __trigger_id FROM trigger_ids_to_delete)"
        )
        self.db.cursor().execute(
            "DELETE FROM trigger_map WHERE __trigger_id IN (SELECT __trigger_id FROM trigger_ids_to_delete)"
        )
        self.db.cursor().execute("DROP TABLE event_ids_to_save")
        self.db.cursor().execute("DROP TABLE trigger_ids_to_delete")
        self.db.commit()
        self.db.cursor().execute("VACUUM;")

    def cluster_final(self, win_in_sec=1.0, column="network_snr"):
        """
        Final round of clustering.
        """
        # FIXME: Is there a smarter way?
        event_ids_to_delete = []
        previous_row = None
        for row in self.db.cursor().execute(
            f"SELECT __event_id, time*1e-9 as timesec, {column} FROM event ORDER BY time;"
        ):
            time = dict(row)["timesec"]
            event_id = dict(row)["__event_id"]
            if previous_row is None:
                previous_row = row
                continue
            elif time - dict(previous_row)["timesec"] < win_in_sec:
                if dict(row)[f"{column}"] > dict(previous_row)[f"{column}"]:
                    event_ids_to_delete.append(dict(previous_row)["__event_id"])
                    previous_row = row
                else:
                    event_ids_to_delete.append(dict(row)["__event_id"])
            else:
                previous_row = row

        if not event_ids_to_delete:
            return

        self.db.cursor().execute(
            "CREATE TEMPORARY TABLE event_ids_to_delete (event_id INTEGER);"
        )
        for event_id in event_ids_to_delete:
            self.db.cursor().execute(
                "INSERT INTO event_ids_to_delete(event_id) VALUES (%s);" % event_id
            )

        # Delets all the stuff that doesn't survive clustering
        self.db.cursor().execute(
            "CREATE TEMPORARY TABLE trigger_ids_to_delete AS SELECT __trigger_id FROM trigger_map WHERE __event_id IN (SELECT event_id FROM event_ids_to_delete)"
        )
        self.db.cursor().execute(
            "DELETE FROM event WHERE __event_id IN (SELECT event_id FROM event_ids_to_delete)"
        )
        self.db.cursor().execute(
            "DELETE FROM trigger WHERE __trigger_id IN (SELECT __trigger_id FROM trigger_ids_to_delete)"
        )
        self.db.cursor().execute(
            "DELETE FROM trigger_map WHERE __trigger_id IN (SELECT __trigger_id FROM trigger_ids_to_delete)"
        )
        self.db.cursor().execute("DROP TABLE event_ids_to_delete")
        self.db.cursor().execute("DROP TABLE trigger_ids_to_delete")
        self.db.commit()
        self.db.cursor().execute("VACUUM;")


# Function to select data from the first database
def select_data_from_db(cursor, table_name):
    # Select all rows from the specified table
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    return rows


# Function to insert data into the second database
def insert_ignore(cursor, table_name, rows, column_names):

    # Prepare the SQL insert statement based on the column count
    placeholders = ", ".join(["?"] * len(column_names))
    insert_query = f"INSERT OR IGNORE INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"

    # Insert each row into the second database
    cursor.executemany(insert_query, rows)
