from os import getenv
import unittest
from pprint import pprint
import psycopg2
from modules.SweetiePings import PingStoragePg, PingStorageRedis
from modules.FakeRedis import FakeRedis

pg_conn_str = getenv('SB_PG_DB', None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")

class TellStorageTests(object):
    def test_returns_empty_members_list(self):
        result = self.impl.get_ping_group_members("empty_group")
        self.assertListEqual([], result)
    
    def test_returns_members_list_containing_member(self):
        self.impl.add_ping_group_member("group", "member1")
        result = self.impl.get_ping_group_members("group")
        self.assertListEqual(["member1"], result)

    def test_adding_group_member_is_idempotent(self):
        v1 = self.impl.add_ping_group_member("group", "member1")
        v2 = self.impl.add_ping_group_member("group", "member1")
        self.assertTrue(v1)
        self.assertFalse(v2) # member already added
        result = self.impl.get_ping_group_members("group")
        self.assertListEqual(["member1"], result)
    
    def test_removing_group_member(self):
        self.impl.add_ping_group_member("evil_horde", "adora")
        self.impl.add_ping_group_member("evil_horde", "catra")
        self.impl.remove_ping_group_member("evil_horde", "adora")

        result = self.impl.get_ping_group_members("evil_horde")
        self.assertListEqual(["catra"], result)
    
    def test_removing_group_member_from_empty_group_does_nothing(self):
        v1 = self.impl.remove_ping_group_member("group", "member1")
        self.assertFalse(v1)
        result = self.impl.get_ping_group_members("group")
        self.assertListEqual([], result)
    
    def test_listing_groups(self):
        result = self.impl.get_ping_group_list()
        self.assertListEqual([], result)

        self.impl.add_ping_group_member("人間", "みちる")
        self.impl.add_ping_group_member("獣人", "みちる")
        self.impl.add_ping_group_member("獣人", "しろう")
        
        result = self.impl.get_ping_group_list()
        self.assertListEqual([("人間", 1), ("獣人", 2)], result)

    def test_listing_groups_ignores_empty_groups(self):
        self.impl.add_ping_group_member("evil horde", "catra")
        self.impl.remove_ping_group_member("evil horde", "catra")

        result = self.impl.get_ping_group_list()
        self.assertListEqual([], result)
    
    def test_get_groups_for_member(self):
        self.impl.add_ping_group_member("人間", "みちる")
        self.impl.add_ping_group_member("獣人", "みちる")

        result = self.impl.get_ping_groups_for_member("みちる")
        self.assertListEqual(["人間", "獣人"], result)

class TellStoragePgTests(TellStorageTests, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with psycopg2.connect(pg_conn_str) as conn, conn.cursor() as cur:
            conn.autocommit = True
            cur.execute("CREATE DATABASE ping_storage_tests")
        cls.conn = psycopg2.connect(pg_conn_str, dbname="ping_storage_tests")
        cls.impl = PingStoragePg(cls.conn)
    
    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        with psycopg2.connect(pg_conn_str) as conn, conn.cursor() as cur:
            conn.autocommit = True
            cur.execute("DROP DATABASE ping_storage_tests")
    
    def setUp(self):
        with self.conn.cursor() as cur:
            # TODO: should this be able to run the sql in create_basic_tables somehow?
            cur.execute("DROP TABLE IF EXISTS ping_group_memberships;"
                        "CREATE TABLE ping_group_memberships("
                        "    member_jid TEXT, "
                        "    group_name TEXT, "
                        "    PRIMARY KEY (member_jid, group_name) "
                        ");")
            self.conn.commit()

class TellStorageRedisTests(TellStorageTests, unittest.TestCase):
    def setUp(self):
        self.impl = PingStorageRedis(FakeRedis())