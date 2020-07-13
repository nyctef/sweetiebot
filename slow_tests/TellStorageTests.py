from os import getenv
import unittest
from pprint import pprint
import psycopg2
from modules.SweetieTell import TellStoragePg, TellStorageRedis
from modules.FakeRedis import FakeRedis

pg_conn_str = getenv('SB_PG_DB', None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")

class TellStorageTests(object):
    def test_impl_is_not_none(self):
        self.assertIsNotNone(self.impl)
    
    def test_jid_from_nick_returns_none_if_not_found(self):
        self.assertEqual(None, self.impl.get_jid_from_nick("not_found"))
    
    def test_jid_from_nick_returns_result_if_found(self):
        self.impl.set_jid_for_nick("nick1", "jid1")
        self.assertEqual("jid1", self.impl.get_jid_from_nick("nick1"))
    
    def test_jid_from_nick_returns_latest_result(self):
        self.impl.set_jid_for_nick("nick1", "jid1")
        self.impl.set_jid_for_nick("nick1", "jid2")
        self.assertEqual("jid2", self.impl.get_jid_from_nick("nick1"))


class TellStoragePgTests(TellStorageTests, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with psycopg2.connect(pg_conn_str) as conn, conn.cursor() as cur:
            conn.autocommit = True
            cur.execute("CREATE DATABASE tell_storage_tests")
        cls.conn = psycopg2.connect(pg_conn_str, dbname="tell_storage_tests")
        cls.impl = TellStoragePg(cls.conn)
    
    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        with psycopg2.connect(pg_conn_str) as conn, conn.cursor() as cur:
            conn.autocommit = True
            cur.execute("DROP DATABASE tell_storage_tests")
    
    def setUp(self):
        with self.conn.cursor() as cur:
            # TODO: should this be able to run the sql in create_basic_tables somehow?
            cur.execute("DROP TABLE IF EXISTS tell_jid_to_nick_mapping;"
                        "DROP TABLE IF EXISTS tell_messages_by_sender;"
                        "CREATE TABLE tell_jid_to_nick_mapping(nick TEXT PRIMARY KEY, jid TEXT);"
                        "CREATE TABLE tell_messages_by_sender(sender_jid TEXT, receiver_jid TEXT, messages TEXT[], PRIMARY KEY (sender_jid, receiver_jid));")
            self.conn.commit()

class TellStorageRedisTests(TellStorageTests, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.impl = TellStorageRedis(FakeRedis())