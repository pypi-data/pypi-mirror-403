import os
import logging

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection

from typing import NamedTuple, List, Optional
from timescaler.constants import (
    CHUNK_SNAP_COLUMNS,
    SNAPSHOT_TABLE,
    SNAPSHOT_SCHEMA
)

logger = logging.getLogger(__name__)

class Hypertable(NamedTuple):
    schema: str
    name: str

class Timescaler:

    #####################################################################################
    ################ Methods to establish a connection to the databases #################

    @classmethod
    def _is_connection_robust(cls):
        if not hasattr(cls, "_postgres_conn") or cls._postgres_conn is None:
            return False
        if cls._postgres_conn.closed != 0:
            return False
        try:
            with cls._postgres_conn as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True
        except Exception:
            return False

    @classmethod
    def _get_postgres_connection(cls) -> connection:
        if cls._is_connection_robust():
            return cls._postgres_conn
        
        host = os.getenv("TIMESCALEDB_HOST")
        port = os.getenv("TIMESCALEDB_PORT")
        username = os.getenv("TIMESCALEDB_USERNAME")
        password = os.getenv("TIMESCALEDB_PASSWORD")
        database = os.getenv("TIMESCALEDB_NAME")
        cls._postgres_conn = psycopg2.connect(
            host=host, dbname=database, user=username, password=password, port=port
        )
        return cls._postgres_conn

    @classmethod
    def get_chunk_metadata(cls, hypertables: List[Hypertable] = None):
        with cls._get_postgres_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # If hypertables provided, we could filter in SQL for efficiency
                if hypertables:
                    # Construct tuple list for IN clause or similar. 
                    # Postgres (a,b) IN ((x,y), ...) syntax works.
                    conditions_sql = ",".join([f"('{ht.schema}', '{ht.name}')" for ht in hypertables])
                    cur.execute(
                        f"SELECT * FROM timescaledb_information.chunks WHERE (hypertable_schema, hypertable_name) IN ({conditions_sql})"
                    )
                else:
                    cur.execute(
                        f"SELECT * FROM timescaledb_information.chunks"
                    )
                res = cur.fetchall()
                if len(res) == 0:
                    logger.warning("No chunks found")
        return res

    @classmethod
    def get_hypertables(cls) -> List[Hypertable]:
        with cls._get_postgres_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT hypertable_schema, hypertable_name FROM timescaledb_information.hypertables"
                )
                res = cur.fetchall()
        return [Hypertable(schema=r['hypertable_schema'], name=r['hypertable_name']) for r in res]

    @classmethod
    def get_chunk_compression_stats(cls, hypertables: List[Hypertable] = None):
        if hypertables is None:
            hypertables = cls.get_hypertables()
        results = []
        with cls._get_postgres_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for ht in hypertables:
                    try:
                        cur.execute(
                            f"SELECT *, '{ht.schema}' as hypertable_schema, '{ht.name}' as hypertable_name FROM chunk_columnstore_stats('{ht.schema}.{ht.name}')"
                        )
                        rows = cur.fetchall()
                        results.extend(rows)
                    except Exception as e:
                        logger.warning(f"Error fetching chunk compression stats for {ht.schema}.{ht.name}: {e}")
                        conn.rollback()
        return results

    @classmethod
    def get_hypertable_metadata(cls, hypertables: List[Hypertable] = None):
        with cls._get_postgres_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if hypertables:
                    conditions_sql = ",".join([f"('{ht.schema}', '{ht.name}')" for ht in hypertables])
                    cur.execute(
                        f"SELECT * FROM timescaledb_information.hypertables WHERE (hypertable_schema, hypertable_name) IN ({conditions_sql})"
                    )
                else:
                    cur.execute(
                        "SELECT * FROM timescaledb_information.hypertables"
                    )
                res = cur.fetchall()
                if len(res) == 0:
                    logger.warning("No hypertables found")
        return res

    @classmethod
    def get_hypertable_compression_stats(cls, hypertables: List[Hypertable] = None):
        if hypertables is None:
            hypertables = cls.get_hypertables()
        results = []
        with cls._get_postgres_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for ht in hypertables:
                    try:
                        cur.execute(
                            f"SELECT *, '{ht.schema}' as hypertable_schema, '{ht.name}' as hypertable_name FROM hypertable_columnstore_stats('{ht.schema}.{ht.name}')"
                        )
                        rows = cur.fetchall()
                        results.extend(rows)
                    except Exception as e:
                        logger.warning(f"Error fetching hypertable compression stats for {ht.schema}.{ht.name}: {e}")
                        conn.rollback()
        return results

    @classmethod
    def get_hypertable_size(cls, hypertables: List[Hypertable] = None):
        if hypertables is None:
            hypertables = cls.get_hypertables()
        results = []
        with cls._get_postgres_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for ht in hypertables:
                    try:
                        cur.execute(
                            f"SELECT *, '{ht.schema}' as hypertable_schema, '{ht.name}' as hypertable_name FROM hypertable_detailed_size('{ht.schema}.{ht.name}')"
                        )
                        rows = cur.fetchall()
                        results.extend(rows)
                    except Exception as e:
                        logger.warning(f"Error fetching hypertable size for {ht.schema}.{ht.name}: {e}")
                        conn.rollback()
        return results

    @classmethod
    def get_chunks_size(cls, hypertables: List[Hypertable] = None):
        if hypertables is None:
            hypertables = cls.get_hypertables()
        results = []
        with cls._get_postgres_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for ht in hypertables:
                    try:
                        cur.execute(
                            f"SELECT *, '{ht.schema}' as hypertable_schema, '{ht.name}' as hypertable_name FROM chunks_detailed_size('{ht.schema}.{ht.name}')"
                        )
                        rows = cur.fetchall()
                        results.extend(rows)
                    except Exception as e:
                        logger.warning(f"Error fetching chunks size for {ht.schema}.{ht.name}: {e}")
                        conn.rollback()
        return results

    



    @classmethod
    def chunk_details(cls, hypertables: List[Hypertable] = None):
        metadata = cls.get_chunk_metadata(hypertables=hypertables)
        sizes = cls.get_chunks_size(hypertables=hypertables)

        # Create a lookup dict for sizes
        size_lookup = {
            (s['hypertable_schema'], s['hypertable_name'], s['chunk_name']): s
            for s in sizes
        }

        results = []
        for m in metadata:
            key = (m['hypertable_schema'], m['hypertable_name'], m['chunk_name'])
            size_info = size_lookup.get(key, {})
            # Merge logic: metadata first, then size info (overwriting if collision, though keys should be distinct mostly)
            merged = {**m, **size_info}
            results.append(merged)
        
        return results

    @classmethod
    def ensure_chunk_snapshot_table(cls):
        with cls._get_postgres_connection() as conn:
            with conn.cursor() as cur:
                # Create schema if not exists
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SNAPSHOT_SCHEMA};")
                
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {SNAPSHOT_SCHEMA}.{SNAPSHOT_TABLE} (
                        {CHUNK_SNAP_COLUMNS.TIME} TIMESTAMPTZ NOT NULL,
                        {CHUNK_SNAP_COLUMNS.HYPERTABLE_SCHEMA} TEXT NOT NULL,
                        {CHUNK_SNAP_COLUMNS.HYPERTABLE_NAME} TEXT NOT NULL,
                        {CHUNK_SNAP_COLUMNS.CHUNK_NAME} TEXT NOT NULL,
                        {CHUNK_SNAP_COLUMNS.TOTAL_BYTES} BIGINT,
                        {CHUNK_SNAP_COLUMNS.INDEX_BYTES} BIGINT,
                        {CHUNK_SNAP_COLUMNS.TOAST_BYTES} BIGINT,
                        {CHUNK_SNAP_COLUMNS.TABLE_BYTES} BIGINT
                    );
                """)
                # Convert to hypertable if not already (check existence first or ignore error safely)
                # simpler to just try create_hypertable if_not_exists logic if strictly needed, 
                # but standard practice: check if it's a hypertable first.
                cur.execute(
                    "SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = %s", 
                    (f"{SNAPSHOT_SCHEMA}.{SNAPSHOT_TABLE}",)
                )
                # Convert to hypertable if not already using if_not_exists=TRUE to avoid errors/warnings
                try:
                    cur.execute(f"SELECT create_hypertable('{SNAPSHOT_SCHEMA}.{SNAPSHOT_TABLE}', '{CHUNK_SNAP_COLUMNS.TIME}', if_not_exists => TRUE);")
                except Exception as e:
                    # Ignore if it's already a hypertable (though if_not_exists should handle it, older versions might warn)
                    # Actually if_not_exists returns (hypertable_id, schema_name, table_name, created) tuple usually, or void.
                    logger.warning(f"Could not convert snapshot table to hypertable: {e}")
                    conn.rollback()
    
    @classmethod
    def snap(cls, target_hypertables: List[Hypertable] = None):
        """
        Snapshots chunk sizes.
        :param target_hypertables: Optional list of Hypertable(schema, name) tuples to snapshot. 
                                   If None, snapshots all hypertables.
        """
        cls.ensure_chunk_snapshot_table()
        stats = cls.get_chunks_size(hypertables=target_hypertables)
        
        if not stats:
            return

        with cls._get_postgres_connection() as conn:
            with conn.cursor() as cur:
                for row in stats:
                    cur.execute(f"""
                        INSERT INTO {SNAPSHOT_SCHEMA}.{SNAPSHOT_TABLE} (
                            {CHUNK_SNAP_COLUMNS.TIME}, 
                            {CHUNK_SNAP_COLUMNS.HYPERTABLE_SCHEMA}, 
                            {CHUNK_SNAP_COLUMNS.HYPERTABLE_NAME}, 
                            {CHUNK_SNAP_COLUMNS.CHUNK_NAME}, 
                            {CHUNK_SNAP_COLUMNS.TOTAL_BYTES}, 
                            {CHUNK_SNAP_COLUMNS.INDEX_BYTES}, 
                            {CHUNK_SNAP_COLUMNS.TOAST_BYTES}, 
                            {CHUNK_SNAP_COLUMNS.TABLE_BYTES}
                        ) VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row.get(CHUNK_SNAP_COLUMNS.HYPERTABLE_SCHEMA),
                        row.get(CHUNK_SNAP_COLUMNS.HYPERTABLE_NAME),
                        row.get(CHUNK_SNAP_COLUMNS.CHUNK_NAME),
                        row.get(CHUNK_SNAP_COLUMNS.TOTAL_BYTES),
                        row.get(CHUNK_SNAP_COLUMNS.INDEX_BYTES),
                        row.get(CHUNK_SNAP_COLUMNS.TOAST_BYTES),
                        row.get(CHUNK_SNAP_COLUMNS.TABLE_BYTES)
                    ))


if __name__ == "__main__":
    from pprint import pprint
    pprint(TimeSquare.get_chunk_metadata())
