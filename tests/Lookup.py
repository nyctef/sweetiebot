from modules import Message, SweetieLookup
import unittest
from unittest.mock import MagicMock

def create_message(input, is_pm=False):
    return Message('Sweetiebot', 'sender', 'chat@jabber.org/sender', 'sender@jabber.org', input, input, is_pm)

class LookupTests(unittest.TestCase):

    def setUp(self):
        self.bot = MagicMock()
        self.lookup = SweetieLookup(self.bot)

    def test_can_roll_simple_dice(self):
        message = create_message('!roll 1d20')
        response = self.lookup.roll(message)

        self.assertIsNotNone(response)


