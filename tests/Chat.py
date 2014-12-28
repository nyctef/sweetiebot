from modules import Message, SweetieChat
import unittest
from unittest.mock import MagicMock, patch

def create_message(input, is_pm=False):
    return Message('Sweetiebot', 'sender', 'chat@jabber.org/sender', 'sender@jabber.org', input, input, is_pm)

class SweetieChatTests(unittest.TestCase):

    def setUp(self):
        self.bot = MagicMock()
        self.actions = MagicMock()
        self.sass = MagicMock()
        self.chatroom = MagicMock()
        self.markov = MagicMock()

        self.chat = SweetieChat(self.bot, self.actions, self.sass,
                self.chatroom, self.markov)

    def test_can_choose_a_thing(self):
        response = self.chat.choose(create_message('!choose pizza,pie,calzone'))
        self.assertIn(response, ['pizza', 'pie', 'calzone'])
