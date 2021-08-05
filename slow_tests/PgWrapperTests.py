import unittest
from os import getenv
import psycopg2

from modules import PgWrapper

pg_conn_str = getenv("SB_PG_DB", None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")

class PgWrapperTests(unittest.TestCase):
    def test_handles_when_connection_is_disconnected(self):
        dbwrapper = PgWrapper(pg_conn_str)

        self.assertEqual(1, dbwrapper.query_one("SELECT 1;"))

        # now we sneakily poke inside dbwrapper and fake a random network disconnection
        dbwrapper._conn.close()

        # but dbwrapper should recover
        self.assertEqual(1, dbwrapper.query_one("SELECT 1;"))
    
    def test_handles_connection_in_failed_state(self):
        dbwrapper = PgWrapper(pg_conn_str)

        self.assertEqual(1, dbwrapper.query_one("SELECT 1;"))

        # running some invalid sql puts the transaction into a failed state:
        self.assertRaises(
            psycopg2.errors.UndefinedTable, 
            lambda: dbwrapper.query_all("SELECT * FROM nonexistent_table;"))

        # but dbwrapper should recover
        self.assertEqual(1, dbwrapper.query_one("SELECT 1;"))