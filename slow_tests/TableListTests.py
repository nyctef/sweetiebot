from os import getenv
import unittest
from pprint import pprint
import psycopg2

pg_conn_str = getenv('SB_PG_DB', None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")

class TableList(unittest.TestCase):
    def test_something(self):
        conn = psycopg2.connect(pg_conn_str)
        cur = conn.cursor()
        cur.execute("SELECT text FROM deowl_fails;")
        pprint(cur.fetchone()[0])
        pprint(cur.fetchone()[0])