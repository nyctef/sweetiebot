from os import getenv
import unittest
import psycopg2
from modules.TableList import TableList, RandomizedList
from modules import PgWrapper

pg_conn_str = getenv("SB_PG_DB", None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")


class TableListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conn = psycopg2.connect(pg_conn_str)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DROP DATABASE IF EXISTS table_list_tests")
        cur.execute("CREATE DATABASE table_list_tests")

        cls.dbwrapper = PgWrapper(pg_conn_str + " dbname=table_list_tests")

    @classmethod
    def tearDownClass(cls):
        cls.dbwrapper._conn.close()

        conn = psycopg2.connect(pg_conn_str)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DROP DATABASE table_list_tests")

    def setUp(self):
        self.dbwrapper.write(
            "DROP TABLE IF EXISTS deowl_fails;"
            "CREATE TABLE deowl_fails(id serial PRIMARY KEY, text TEXT UNIQUE NOT NULL);"
        )

    def test_loops_through_list_when_reaches_end(self):
        tablelist = RandomizedList(TableList(self.dbwrapper, "deowl_fails"))
        self.dbwrapper.write("INSERT INTO deowl_fails(text) VALUES ('test1')")

        value1 = tablelist.get_next()
        value2 = tablelist.get_next()

        self.assertEqual(value1, value2)
        self.assertIsNotNone(value2)

    def test_throws_error_if_no_results_found(self):
        """TODO: should this just return None instead?"""
        tablelist = RandomizedList(TableList(self.dbwrapper, "deowl_fails"))

        with self.assertRaises(Exception):
            tablelist.get_next()

    def test_remembers_new_lines_added(self):
        tablelist = RandomizedList(TableList(self.dbwrapper, "deowl_fails"))

        tablelist.add_line("this is a new line")

        # make sure any changes were committed to the db
        self.dbwrapper._conn.rollback()

        value1 = tablelist.get_next()

        self.assertEqual("this is a new line", value1)
