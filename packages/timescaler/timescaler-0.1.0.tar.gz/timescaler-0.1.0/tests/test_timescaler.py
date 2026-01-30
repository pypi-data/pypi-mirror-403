import unittest
from testcontainers.postgres import PostgresContainer
from testcontainers.core.container import DockerContainer
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from timescaler.main import Timescaler, Hypertable
from timescaler.constants import CHUNK_SNAP_COLUMNS, SNAPSHOT_TABLE, SNAPSHOT_SCHEMA
from timescaler.decorator import snap_stats
import time

class TimescaleContainer(PostgresContainer):
    def __init__(self, image="timescale/timescaledb:latest-pg14", **kwargs):
        super().__init__(image=image, **kwargs)

class LokiContainer(DockerContainer):
    def __init__(self, image="grafana/loki:latest", **kwargs):
        super().__init__(image=image, **kwargs)
        self.with_exposed_ports(3100)
    
    def get_loki_url(self):
        host = self.get_container_host_ip()
        port = self.get_exposed_port(3100)
        return f"http://{host}:{port}/loki/api/v1/push"

class TestTimescaler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.postgres = TimescaleContainer()
        cls.postgres.start()
        
        cls.loki = LokiContainer()
        cls.loki.start()
        
        # Override environment variables for Timescaler connection
        os.environ["TIMESCALEDB_HOST"] = cls.postgres.get_container_host_ip()
        os.environ["TIMESCALEDB_PORT"] = str(cls.postgres.get_exposed_port(5432))
        os.environ["TIMESCALEDB_USERNAME"] = cls.postgres.username
        os.environ["TIMESCALEDB_PASSWORD"] = cls.postgres.password
        os.environ["TIMESCALEDB_NAME"] = cls.postgres.dbname
        
        # Override LOKI_URL
        os.environ["LOKI_URL"] = cls.loki.get_loki_url()
        
        # Re-run setup to ensure logger picks up new env if it hasn't already or to re-configure
        # Since setup_loki_logging checks for duplicate handlers, it might return early if imported already.
        # But we want it to point to the NEW url. 
        # The Handler is already attached with localhost:3100 if __init__ ran on import.
        # We might need to force re-configure.
        from timescaler.logger import setup_loki_logging
        import logging
        # Remove old Loki handler if exists to update URL
        logger = logging.getLogger("timescaler")
        for h in list(logger.handlers):
             # Simple check by name or type if we imported it
             if "LokiHandler" in str(type(h)):
                  logger.removeHandler(h)
        setup_loki_logging()

        # Initialize DB with some data
        conn = psycopg2.connect(
            host=cls.postgres.get_container_host_ip(),
            port=cls.postgres.get_exposed_port(5432),
            user=cls.postgres.username,
            password=cls.postgres.password,
            dbname=cls.postgres.dbname
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            # Enable TimescaleDB extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            
            # Create a dummy table and convert to hypertable
            cur.execute("CREATE TABLE conditions (time TIMESTAMPTZ NOT NULL, location TEXT, temperature DOUBLE PRECISION);")
            cur.execute("SELECT create_hypertable('conditions', 'time');")
            
            # Insert some dummy data
            cur.execute("INSERT INTO conditions(time, location, temperature) VALUES (NOW(), 'office', 70.0);")
            cur.execute("INSERT INTO conditions(time, location, temperature) VALUES (NOW(), 'basement', 60.0);")

            # Create a second dummy table for testing selective snap
            cur.execute("CREATE TABLE conditions_2 (time TIMESTAMPTZ NOT NULL, location TEXT, temperature DOUBLE PRECISION);")
            cur.execute("SELECT create_hypertable('conditions_2', 'time');")
            cur.execute("INSERT INTO conditions_2(time, location, temperature) VALUES (NOW(), 'garage', 50.0);")
        
        conn.close()

    @classmethod
    def tearDownClass(cls):
        # Close the connection held by the Timescaler class if it exists
        if hasattr(Timescaler, "_postgres_conn") and Timescaler._postgres_conn is not None:
            Timescaler._postgres_conn.close()
            Timescaler._postgres_conn = None

        cls.postgres.stop()
        cls.loki.stop()
        
        # Clean up env vars
        os.environ.pop("TIMESCALEDB_HOST", None)
        os.environ.pop("TIMESCALEDB_PORT", None)
        os.environ.pop("TIMESCALEDB_USERNAME", None)
        os.environ.pop("TIMESCALEDB_PASSWORD", None)
        os.environ.pop("TIMESCALEDB_NAME", None)
        os.environ.pop("LOKI_URL", None)

    def test_connection_robustness(self):
        # Ensure our class can connect to the test container
        # Reset any cached connection
        Timescaler._postgres_conn = None
        self.assertFalse(Timescaler._is_connection_robust()) # Initially false or re-checked
        conn = Timescaler._get_postgres_connection()
        self.assertIsNotNone(conn)
        self.assertTrue(Timescaler._is_connection_robust())

    def test_logging_setup(self):
        import logging
        logger = logging.getLogger("timescaler")
        handlers = logger.handlers
        loki_handlers = [h for h in handlers if "LokiHandler" in str(type(h))]
        self.assertTrue(len(loki_handlers) > 0, "LokiHandler should be attached to timescaler logger")
        
        # Optional: Send a log message
        logger.info("Test log message from test_timescaler")
        # To verify it arrived in Loki would require querying Loki API, which is complex and might be flaky due to async ingestion.
        # Just verifying the handler is present is a good start.

    def test_get_hypertables(self):
        hypertables = Timescaler.get_hypertables()
        self.assertGreaterEqual(len(hypertables), 1)
        self.assertIsInstance(hypertables[0], Hypertable)
        self.assertEqual(hypertables[0].name, 'conditions')

    def test_get_hypertable_metadata(self):
        metadata = Timescaler.get_hypertable_metadata()
        self.assertGreaterEqual(len(metadata), 1)
        # Check for keys returned by timescaledb_information.hypertables
        self.assertIn('hypertable_schema', metadata[0])
        self.assertIn('hypertable_name', metadata[0])

    def test_chunk_details(self):
        # This might return empty if chunks haven't been created yet (requires enough data or time passage)
        # But we can at least verify the method runs without error and returns a list
        details = Timescaler.chunk_details()
        self.assertIsInstance(details, list)
        
        # If chunks exist, verify structure
        if len(details) > 0:
            self.assertIn('chunk_name', details[0])
            self.assertIn('total_bytes', details[0]) # From joined size info

    def test_get_chunk_compression_stats(self):
        # We haven't enabled compression on the dummy table, so this might be empty/error-free
        stats = Timescaler.get_chunk_compression_stats()
        self.assertIsInstance(stats, list)

    def test_get_hypertable_size(self):
        sizes = Timescaler.get_hypertable_size()
        self.assertGreaterEqual(len(sizes), 1)
        self.assertIn('total_bytes', sizes[0])
        self.assertEqual(sizes[0]['hypertable_name'], 'conditions')

    def test_snap_functionality(self):
        # 1. Take a snapshot
        Timescaler.snap()
        
        # 2. Verify data exists in the snapshot table
        conn = Timescaler._get_postgres_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {SNAPSHOT_SCHEMA}.{SNAPSHOT_TABLE}")
            rows = cur.fetchall()
            
            # Since we inserted enough data to force chunk creation? 
            # Note: The 'conditions' table in setUpClass has inserts. 
            # TimescaleDB usually creates chunks on insert.
            # However, if data is small, it might be in one chunk or just in the main table depending on configuration?
            # Actually create_hypertable usually implies chunking.
            # get_chunks_size() relies on chunks existing.
            
            # If get_chunks_size() returns data, snap() should insert data.
            chunks = Timescaler.get_chunks_size()
            if chunks:
                self.assertGreaterEqual(len(rows), 1)
                self.assertEqual(rows[0][CHUNK_SNAP_COLUMNS.HYPERTABLE_NAME], 'conditions')
                self.assertIsNotNone(rows[0][CHUNK_SNAP_COLUMNS.TIME])
                self.assertIn(CHUNK_SNAP_COLUMNS.TOTAL_BYTES, rows[0])
            else:
                # If no chunks, snap is empty, but table should exist
                # Verify table existence by the fact query didn't fail
                pass

    def test_snap_selective(self):
        # 1. Take a selective snapshot only for 'conditions'
        html_conditions = Hypertable(schema='public', name='conditions')
        html_conditions2 = Hypertable(schema='public', name='conditions_2')

        Timescaler.ensure_chunk_snapshot_table()
        conn = Timescaler._get_postgres_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"TRUNCATE {SNAPSHOT_SCHEMA}.{SNAPSHOT_TABLE}")
            
        Timescaler.snap([html_conditions])
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT DISTINCT {CHUNK_SNAP_COLUMNS.HYPERTABLE_NAME} FROM {SNAPSHOT_SCHEMA}.{SNAPSHOT_TABLE}")
            rows = cur.fetchall()
            names = [r[CHUNK_SNAP_COLUMNS.HYPERTABLE_NAME] for r in rows]
            
            self.assertIn('conditions', names)
            self.assertNotIn('conditions_2', names)
            
        # Test snapping the other one
        Timescaler.snap([html_conditions2])
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {SNAPSHOT_SCHEMA}.{SNAPSHOT_TABLE} WHERE {CHUNK_SNAP_COLUMNS.HYPERTABLE_NAME} = 'conditions_2'")
            rows = cur.fetchall()
            
            # We strictly expect chunks to exist for conditions_2 as well
            self.assertGreaterEqual(len(rows), 1)
            
    def test_chunk_details_filtered(self):
        # Selective chunk details
        html_conditions = Hypertable(schema='public', name='conditions')
        details = Timescaler.chunk_details(hypertables=[html_conditions])
        # Should only contain 'conditions' stuff. 
        # But chunk details returns list of dictionaries with merged info. 
        # The underlying queries filter by hypertable.
        # We can check if any returned item belongs to conditions_2 (if it has chunks)
        # Assuming conditions_2 has chunks (it had inserts)
        # Actually in test_snap_selective, we saw that conditions_2 might not have chunks if data is small?
        # But we can verify that we DON'T get error and return type is correct.
        self.assertIsInstance(details, list)
        if len(details) > 0:
            for d in details:
                 self.assertEqual(d.get('hypertable_name'), 'conditions')

    def test_get_chunk_metadata_filtered(self):
        html_conditions = Hypertable(schema='public', name='conditions')
        metadata = Timescaler.get_chunk_metadata(hypertables=[html_conditions])
        self.assertIsInstance(metadata, list)
        for m in metadata:
            self.assertEqual(m.get('hypertable_name'), 'conditions')

    def test_get_hypertable_metadata_filtered(self):
        html_conditions = Hypertable(schema='public', name='conditions')
        metadata = Timescaler.get_hypertable_metadata(hypertables=[html_conditions])
        # Should be exactly 1
        self.assertEqual(len(metadata), 1)
        self.assertEqual(metadata[0].get('hypertable_name'), 'conditions')
    
    def test_get_hypertable_size_filtered(self):
        html_conditions = Hypertable(schema='public', name='conditions')
        sizes = Timescaler.get_hypertable_size(hypertables=[html_conditions])
        self.assertEqual(len(sizes), 1)
        self.assertEqual(sizes[0].get('hypertable_name'), 'conditions')

    def test_decorator_usage(self):
        # 1. Clear snapshot table
        # Ensure it exists first, as other tests might not have run or order is random (though usually alphabetical/definition order).
        # Actually unittest execution order defaults to alphabetical string sort of method name.
        # But robust tests shouldn't depend on order.
        Timescaler.ensure_chunk_snapshot_table()
        
        conn = Timescaler._get_postgres_connection()
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE {SNAPSHOT_SCHEMA}.{SNAPSHOT_TABLE}")
        
        # 2. Define decorated function
        @snap_stats
        def insert_data():
            with Timescaler._get_postgres_connection() as conn:
                with conn.cursor() as cur:
                     cur.execute("INSERT INTO conditions(time, location, temperature) VALUES (NOW(), 'decorator_test', 80.0);")
        
        # 3. Call it
        insert_data()
        
        # 4. Verify snapshot taken
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {SNAPSHOT_SCHEMA}.{SNAPSHOT_TABLE}")
            rows = cur.fetchall()
            self.assertGreaterEqual(len(rows), 1)
            
        # 5. Test with arguments
        # NOTE: We do NOT truncate here, so we can verify cumulative snapshots
        # with conn.cursor() as cur:
        #    cur.execute(f"TRUNCATE {SNAPSHOT_TABLE}")
            
        html_conditions = Hypertable(schema='public', name='conditions')
        
        @snap_stats(hypertables=[html_conditions])
        def do_nothing():
            pass
            
        do_nothing()
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {SNAPSHOT_SCHEMA}.{SNAPSHOT_TABLE} WHERE {CHUNK_SNAP_COLUMNS.HYPERTABLE_NAME} = 'conditions'")
            rows = cur.fetchall()
            
            # Should have at least 2 rows for 'conditions' (one from first snap, one from second)
            # Assuming 'conditions' has at least 1 chunk.
            self.assertGreaterEqual(len(rows), 2)
            
            # Verify conditions_2 count (should be from first snap only, so >=1 but likely not increased by second snap)
            # But since first snap was "snap all", it snapped conditions_2.
            # Second snap (filtered) snapped only conditions.
            # So conditions_2 count should equal what it was after first snap.
            # Let's just focus on user's request: check 2 rows for html_conditions.
            pass


if __name__ == '__main__':
    unittest.main()
