from modules import Message, SweetieSeen
import unittest
from unittest.mock import MagicMock, patch
from pprint import pprint
from datetime import datetime

def create_message(input, is_pm=False):
    return Message('Sweetiebot', 'sender', 'chat@jabber.org/sender', 'sender@jabber.org', input, input, is_pm)

class SweetieSeenTests(unittest.TestCase):
    def setUp(self):
        pass
        
    def get_time_ago(self, now, past):
        return SweetieSeen.get_time_ago(None, now, past)

    def test_can_print_several_days_ago(self):
        now = datetime(2016, 4, 10, 10, 30)
        past = datetime(2016, 4, 7, 10, 30)
        result = self.get_time_ago(now, past)
        self.assertEqual('3d 0h 0m 0s ago', result)

    def test_can_print_several_minutes_ago(self):
        now = datetime(2016, 4, 10, 10, 30, 31)
        past = datetime(2016, 4, 10, 10, 27, 30)
        result = self.get_time_ago(now, past)
        self.assertEqual('0d 0h 3m 1s ago', result)
