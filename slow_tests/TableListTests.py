from os import getenv
import unittest
from pprint import pprint
import psycopg2
from modules.TableList import TableList

pg_conn_str = getenv('SB_PG_DB', None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")
conn = psycopg2.connect(pg_conn_str)

class TableListTests(unittest.TestCase):
    def test_something(self):
        l = TableList(conn, "deowl_fails")
        print(l.get_next())
        print(l.get_next())