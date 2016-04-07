from modules import Message, SweetieChat
import unittest
from unittest.mock import MagicMock, patch
from pprint import pprint

def create_message(input, is_pm=False):
    return Message('Sweetiebot', 'sender', 'chat@jabber.org/sender', 'sender@jabber.org', input, input, is_pm)

class SweetieChatTests(unittest.TestCase):

    def setUp(self):
        self.bot = MagicMock()
        self.actions = MagicMock()
        self.sass = MagicMock()
        self.chatroom = MagicMock()
        self.markov = MagicMock()
        self.cadmusic = MagicMock()
        self.tell = MagicMock()
        self.tell.get_messages_for = MagicMock(return_value=None)

        self.chat = SweetieChat(self.bot, self.actions, self.sass,
                self.chatroom, self.markov, self.cadmusic, self.tell)

    def test_can_choose_a_thing(self):
        response = self.chat.choose(create_message('!choose pizza,pie,calzone'))
        self.assertIn(response, ['pizza', 'pie', 'calzone'])

    def test_does_not_show_permission_failed_title(self):
        response = self.chat.random_chat(create_message('https://forum.pleaseignore.com/topic/83206/'))
        self.assertIsNone(response)
        
