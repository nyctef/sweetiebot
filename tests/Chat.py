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
        self.sass.get_next = MagicMock(name='some sass')
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

    def test_does_not_cd_in_middle_of_word(self):
        response = self.chat.random_chat(create_message('you\'re a medic/doctor, right?'))
        self.assertIsNone(response)

    def test_sweetiebot_yes(self):
        response = self.chat.random_chat(create_message('Sweetiebot no'))
        self.assertEqual('Sweetiebot yes! :sweetieglee:', response)

    def test_how_x_is_y(self):
        response  = self.chat.random_chat(create_message('Sweetiebot: how x is y?'))
        self.assertEqual('sender: y [64.21% x]', response)
        response2 = self.chat.random_chat(create_message('Sweetiebot: how blue is red'))
        self.assertEqual('sender: red [15.42% blue]', response2)
        response3 = self.chat.random_chat(create_message('Sweetiebot: how amazing are amazing people'))
        self.assertEqual('sender: amazing people [79.86% amazing]', response3)
        response4 = self.chat.random_chat(create_message('Sweetiebot: how totally silly are silly people'))
        self.assertEqual('sender: silly people [45.24% totally silly]', response4)

    def test_misc(self):
        print(self.chat.random_chat(create_message('Sweetiebot: how do you do?')))
        print(self.chat.random_chat(create_message('Sweetiebot: how do you want to play this?')))
        print(self.chat.random_chat(create_message('Sweetiebot: what is love?')))
        print(self.chat.random_chat(create_message('Sweetiebot: will she ever love me')))
        
