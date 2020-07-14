from modules import Message, SweetieSeen, FakeRedis
from modules.RoomMember import RoomMember, RoomMemberList
import unittest
from unittest.mock import MagicMock, patch
from pprint import pprint
from datetime import datetime
import logging

def create_message(input, is_pm=False):
    room_members = [
            RoomMember('Sweetiebot', 'sweetiebot@jabber.org/asdf', 'owner', 'moderator'),
            RoomMember('test_user', 'testuser@jabber.org/asdf', 'none', 'participant'),
            RoomMember('sender', 'chat@jabber.org/sender', 'none', 'participant'),
        ]
    room_member_list = RoomMemberList(room_members)
    return Message('Sweetiebot', 'sender', 'chat@jabber.org/sender', 'sender@jabber.org', input, input, is_pm, room_member_list)

class SweetieSeenTests(unittest.TestCase):
    def setUp(self):
        self.bot = MagicMock()
        self.bot.get_jid_from_nick = MagicMock(return_value=None)
        self.store = FakeRedis()

        self.seen = SweetieSeen(self.bot, self.store)
        
    def test_can_print_several_days_ago(self):
        now = datetime(2016, 4, 10, 10, 30)
        past = datetime(2016, 4, 7, 10, 30)
        result = SweetieSeen.get_time_ago(None, now, past)
        self.assertEqual('3d 0h 0m 0s ago', result)

    def test_can_print_several_minutes_ago(self):
        now = datetime(2016, 4, 10, 10, 30, 31)
        past = datetime(2016, 4, 10, 10, 27, 30)
        result = SweetieSeen.get_time_ago(None, now, past)
        self.assertEqual('0d 0h 3m 1s ago', result)

    def test_returns_no_data_if_not_seen(self):
        response = self.seen.seen(create_message("!seen obi-wan"))

        self.assertEqual(response, "No records found for user 'obi-wan'")
    
    def test_returns_last_spoke_if_spoke_set(self):
        # TODO: this is a pretty nasty set of mock setups
        self.bot.get_jid_from_nick = MagicMock(return_value="sender@jabber.org")
        self.bot.jid_is_in_room = MagicMock(return_value=True)
        message = create_message("test_message")
        self.seen.on_message(message)

        response = self.seen.seen(create_message("!seen sender"))
        
        self.assertRegex(response, "sender last seen speaking at ")
    
    def test_returns_last_spoke_if_spoke_set(self):
        # "seen" is a bit easier to satisfy, since the target doesn't need to be in the room
        presence = MagicMock()
        presence.presence_type = "unavailable"
        presence.muc_jid.resource = "obi-wan"
        self.seen.on_presence(presence)

        response = self.seen.seen(create_message("!seen obi-wan"))

        self.assertRegex(response, "obi-wan last seen in room at ")