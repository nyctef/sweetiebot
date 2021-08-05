from os import getenv
import unittest
from pprint import pprint
import psycopg2
from modules.TableList import TableList, RandomizedList

pg_conn_str = getenv("SB_PG_DB", None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")


class TableListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conn = psycopg2.connect(pg_conn_str)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("CREATE DATABASE table_list_tests")

        cls.conn = psycopg2.connect(pg_conn_str, dbname="table_list_tests")

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

        conn = psycopg2.connect(pg_conn_str)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DROP DATABASE table_list_tests")

    def setUp(self):
        with self.conn.cursor() as cur:
            cur.execute(
                "DROP TABLE IF EXISTS deowl_fails;"
                "CREATE TABLE deowl_fails(id serial PRIMARY KEY, text TEXT UNIQUE NOT NULL);"
            )
            self.conn.commit()

    def test_loops_through_list_when_reaches_end(self):
        l = RandomizedList(TableList(self.conn, "deowl_fails"))
        with self.conn.cursor() as cur:
            cur.execute("INSERT INTO deowl_fails(text) VALUES ('test1')")

        value1 = l.get_next()
        value2 = l.get_next()

        self.assertEqual(value1, value2)
        self.assertIsNotNone(value2)

    def test_throws_error_if_no_results_found(self):
        """TODO: should this just return None instead?"""
        l = RandomizedList(TableList(self.conn, "deowl_fails"))

        with self.assertRaises(Exception):
            l.get_next()

    def test_remembers_new_lines_added(self):
        l = RandomizedList(TableList(self.conn, "deowl_fails"))

        l.add_line("this is a new line")

        # make sure any changes were committed to the db
        self.conn.rollback()

        value1 = l.get_next()

        self.assertEqual("this is a new line", value1)
