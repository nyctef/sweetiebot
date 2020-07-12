from os import getenv
import unittest
from pprint import pprint

pg_conn_str = getenv('SB_PG_DB', None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")

class TableList(unittest.TestCase):
    def test_something(self):
        raise Exception("ouch")