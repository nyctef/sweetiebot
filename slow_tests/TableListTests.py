from os import getenv
import unittest
from pprint import pprint
import psycopg2
from modules.TableList import TableList

pg_conn_str = getenv('SB_PG_DB', None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")

class TableListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with psycopg2.connect(pg_conn_str) as conn, conn.cursor() as cur:
            conn.autocommit = True
            cur.execute("CREATE DATABASE table_list_tests")
        cls.conn = psycopg2.connect(pg_conn_str, dbname="table_list_tests")
    
    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        with psycopg2.connect(pg_conn_str) as conn, conn.cursor() as cur:
            conn.autocommit = True
            cur.execute("DROP DATABASE table_list_tests")
    
    def setUp(self):
        with self.conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS deowl_fails;"
                        "CREATE TABLE deowl_fails(id serial PRIMARY KEY, text TEXT);"
                        "ALTER TABLE deowl_fails ADD UNIQUE (text);")

    def test_something(self):
        l = TableList(self.conn, "deowl_fails")
        with self.conn.cursor() as cur:
            cur.execute("INSERT INTO deowl_fails(text) VALUES ('test1')")
        print(l.get_next())
        print(l.get_next())