from os import getenv
import unittest
from pprint import pprint
import psycopg2
from modules.SweetieSeen import SeenStoragePg, SeenStorageRedis
from modules.FakeRedis import FakeRedis
from datetime import datetime

pg_conn_str = getenv("SB_PG_DB", None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")


class SeenStorageTests(object):
    def test_should_return_none_when_no_records(self):
        result = self.impl.get_seen("みちる")

        self.assertIsNone(result.seen)
        self.assertIsNone(result.spoke)

    def test_should_save_seen_state(self):
        dt = datetime(2020, 10, 13, 12, 34)
        self.impl.set_last_seen_time("みちる", dt)

        result = self.impl.get_seen("みちる")

        self.assertEqual(dt, result.seen)
        self.assertIsNone(result.spoke)

    def test_should_save_spoke_state(self):
        dt = datetime(2020, 10, 13, 12, 34)
        self.impl.set_last_spoke_time("みちる", dt)

        result = self.impl.get_seen("みちる")

        self.assertIsNone(result.seen)
        self.assertEqual(dt, result.spoke)

    def test_should_update_states(self):
        dt1 = datetime(2020, 10, 13, 12, 11)
        dt2 = datetime(2020, 10, 13, 12, 22)
        dt3 = datetime(2020, 10, 13, 12, 33)

        self.impl.set_last_spoke_time("みちる", dt1)
        self.impl.set_last_seen_time("みちる", dt1)
        self.impl.set_last_spoke_time("みちる", dt2)
        self.impl.set_last_seen_time("みちる", dt3)

        result = self.impl.get_seen("みちる")

        self.assertEqual(dt3, result.seen)
        self.assertEqual(dt2, result.spoke)


class TellStoragePgTests(SeenStorageTests, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with psycopg2.connect(pg_conn_str) as conn, conn.cursor() as cur:
            conn.autocommit = True
            cur.execute("CREATE DATABASE seen_storage_tests")
        cls.conn = psycopg2.connect(pg_conn_str, dbname="seen_storage_tests")
        cls.impl = SeenStoragePg(cls.conn)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        with psycopg2.connect(pg_conn_str) as conn, conn.cursor() as cur:
            conn.autocommit = True
            cur.execute("DROP DATABASE seen_storage_tests")

    def setUp(self):
        with self.conn.cursor() as cur:
            # TODO: should this be able to run the sql in create_basic_tables somehow?
            cur.execute(
                "DROP TABLE IF EXISTS seen_records;"
                "CREATE TABLE seen_records(target TEXT PRIMARY KEY, seen TIMESTAMP NULL, spoke TIMESTAMP NULL);"
            )
            self.conn.commit()


class TellStorageRedisTests(SeenStorageTests, unittest.TestCase):
    def setUp(self):
        self.impl = SeenStorageRedis(FakeRedis())
