from modules import Message, SweetiePings, FakeRedis, Presence
from modules.RoomMember import RoomMember, RoomMemberList
import unittest
from unittest.mock import MagicMock, patch
from pprint import pprint

room_members = [
        RoomMember('Sweetiebot', 'sweetiebot@jabber.org/asdf', 'owner', 'moderator'),
        RoomMember('test_user', 'testuser@jabber.org/asdf', 'none', 'participant'),
        RoomMember('sender', 'chat@jabber.org/sender', 'none', 'participant'),
    ]
room_member_list = RoomMemberList(room_members)

def create_message(input, is_pm=False):
    return Message('Sweetiebot', 'sender', 'chat@jabber.org/sender',
            'sender@jabber.org', input, input, is_pm, room_member_list)

def create_message_zhuli(input, is_pm=False):
    return Message('Sweetiebot', 'ZhuLi', 'chat@jabber.org/zhuli',
            'zhuli@jabber.org', input, input, is_pm, room_member_list)

class PingTests(unittest.TestCase):
    def setUp(self):
        self.bot = MagicMock()
        self.store = FakeRedis()

        self.pings = SweetiePings(self.bot, self.store)

    def test_basic_ping_workflow(self):
        # we start with no groups
        response = self.pings.groups(create_message("!groups"))
        self.assertEqual('Available groups: '+'. See also !users and !mygroups', response)

        # one user subscribes to a group
        response = self.pings.subscribe(create_message_zhuli("!subscribe capable_assistants"))
        self.assertEqual("User zhuli@jabber.org added to group 'capable_assistants'", response)

        # the list of groups can now be queried again
        response = self.pings.groups(create_message("!groups"))
        self.assertEqual('Available groups: capable_assistants (1). See also !users and !mygroups', response)

        # one user lists the set of groups they're subscribed to ...
        response = self.pings.mygroups(create_message_zhuli("!mygroups"))
        self.assertEqual('Your groups: capable_assistants. See also !users and !groups', response)

        # ... but the other user isn't subscribed to anything yet.
        response = self.pings.mygroups(create_message("!mygroups"))
        self.assertEqual('User sender@jabber.org is not currently subscribed to any pingable groups', response)

        # A user now pings the group to send a message
        response = self.pings.ping(create_message("!ping capable_assistants Do the thing!"))
        self.assertEqual("ping sent to 1 users", response)

        # And a user unsubscribes from the group
        response = self.pings.unsubscribe(create_message_zhuli('!unsub capable_assistants'))
        self.assertEqual("User zhuli@jabber.org removed from group 'capable_assistants'", response)

        response = self.pings.mygroups(create_message_zhuli("!mygroups"))
        self.assertEqual('User zhuli@jabber.org is not currently subscribed to any pingable groups', response)
