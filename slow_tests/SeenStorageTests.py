from os import getenv
import unittest
import psycopg2
from modules.SweetieSeen import SeenStoragePg, SeenStorageRedis
from modules.FakeRedis import FakeRedis
from modules import PgWrapper
from datetime import datetime
from typing import Callable

pg_conn_str = getenv("SB_PG_DB", None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")


class SeenStorageTests(object):
    impl: SeenStoragePg | SeenStorageRedis
    # provided by unittest.TestCase in the concrete test classes
    assertEqual: Callable[..., None]
    assertIsNone: Callable[..., None]

    def test_should_return_none_when_no_records(self) -> None:
        result = self.impl.get_seen("みちる")

        self.assertIsNone(result.seen)
        self.assertIsNone(result.spoke)

    def test_should_save_seen_state(self) -> None:
        dt = datetime(2020, 10, 13, 12, 34)
        self.impl.set_last_seen_time("みちる", dt)

        result = self.impl.get_seen("みちる")

        self.assertEqual(dt, result.seen)
        self.assertIsNone(result.spoke)

    def test_should_save_spoke_state(self) -> None:
        dt = datetime(2020, 10, 13, 12, 34)
        self.impl.set_last_spoke_time("みちる", dt)

        result = self.impl.get_seen("みちる")

        self.assertIsNone(result.seen)
        self.assertEqual(dt, result.spoke)

    def test_should_update_states(self) -> None:
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


class SeenStoragePgTests(SeenStorageTests, unittest.TestCase):
    dbwrapper: PgWrapper
    impl: SeenStoragePg

    @classmethod
    def setUpClass(cls) -> None:
        conn = psycopg2.connect(pg_conn_str)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("CREATE DATABASE seen_storage_tests")

        cls.dbwrapper = PgWrapper(pg_conn_str + " dbname=seen_storage_tests")  # type: ignore[operator]
        cls.impl = SeenStoragePg(cls.dbwrapper)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.dbwrapper._conn.close()

        conn = psycopg2.connect(pg_conn_str)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DROP DATABASE seen_storage_tests")

    def setUp(self) -> None:
        self.dbwrapper.write(
            # TODO: should this be able to run the sql in create_basic_tables somehow?
            "DROP TABLE IF EXISTS seen_records;"
            "CREATE TABLE seen_records(target TEXT PRIMARY KEY, seen TIMESTAMP NULL, spoke TIMESTAMP NULL);"
        )


class SeenStorageRedisTests(SeenStorageTests, unittest.TestCase):
    def setUp(self) -> None:
        self.impl = SeenStorageRedis(FakeRedis())
