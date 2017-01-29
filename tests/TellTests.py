from modules import Message, SweetieTell, FakeRedis, Presence
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

def create_message_myself(input, is_pm=False):
    return Message('Sweetiebot', 'myself', 'chat@jabber.org/myself',
            'myself@jabber.org', input, input, is_pm, room_member_list)

class TellTests(unittest.TestCase):

    def get_jid(self, nick):
        if nick == 'myself': return 'myself@jabber.org'
        if nick == 'ZhuLi': return 'zhuli@jabber.org'
        if nick == 'Sweetiebot': return 'sweetiebot@jabber.org'
        if nick == 'sender': return 'sender@jabber.org'

    def setUp(self):
        self.bot = MagicMock()
        self.bot.get_jid_from_nick.side_effect = self.get_jid
        self.store = FakeRedis()

        self.tell = SweetieTell(self.bot, self.store)

    def test_can_tell_someone_a_thing(self):
        response = self.tell.tell(create_message('!tell ZhuLi Do the thing!'))
        self.assertEqual('Message received for zhuli@jabber.org', response)

        response = self.tell.get_messages_for(create_message_zhuli('hello there'))
        self.assertEqual('ZhuLi, sender left you a message: Do the thing!', response)

        response = self.tell.get_messages_for(create_message_myself('anybody left me a message?'))
        self.assertIsNone(response)

        response = self.tell.get_messages_for(create_message_zhuli('another thing'))
        # zhuli shouldn't get pinged a second time
        self.assertIsNone(response)

    def test_denies_telling_someone_two_things(self):
        r1 = self.tell.tell(create_message('!tell ZhuLi Do the thing!'))
        r2 = self.tell.tell(create_message('!tell ZhuLi Do the thing!'))
        self.assertEqual('Sorry, you\'ve already left a message for ZhuLi', r2)

    def test_denies_tell_in_pm(self):
        response = self.tell.tell(create_message('!tell ZhuLi Do another thing!', is_pm=True))
        self.assertEqual('Sorry, you can\'t use !tell in a PM', response)

    def test_denies_tell_self(self):
        response = self.tell.tell(create_message_myself('!tell myself to do a thing'))
        self.assertEqual('Talking to yourself is more efficient in real life than on jabber', response)

    def test_denies_tell_bot(self):
        response = self.tell.tell(create_message_myself('!tell Sweetiebot to do a thing'))
        self.assertEqual('I\'m right here, you know', response)

    def test_denies_tell_to_unknown_person(self):
        response = self.tell.tell(create_message('!tell nobody to do a thing'))
        self.assertEqual('Sorry, I don\'t know who \'nobody\' is', response)

    def test_denies_tell_with_empty_message(self):
        response = self.tell.tell(create_message('!tell ZhuLi'))
        self.assertEqual('A message is required', response)

    def test_can_remember_nicks_not_in_chat(self):
        response = self.tell.tell(create_message('!tell AfkPerson to do a thing'))
        self.assertEqual('Sorry, I don\'t know who \'AfkPerson\' is', response)

        self.tell.nicktojid.on_presence(Presence('general@jabber.org/AfkPerson', 'afkperson@jabber.org', None, None))

        response = self.tell.tell(create_message('!tell AfkPerson to do a thing'))
        self.assertEqual('Message received for afkperson@jabber.org', response)

        
