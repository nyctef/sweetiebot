from modules import Message
import unittest

def create_message(input, is_pm=False):
    return Message('Sweetiebot', 'sender', 'chat@jabber.org/sender', 'sender@jabber.org', input, input, is_pm)

class MessageParsingTests(unittest.TestCase):

    def test_parse_simple_command(self):
        message = create_message('Sweetiebot: roll some dice')
        self.assertEqual(message.command, 'roll')
        self.assertEqual(message.args, 'some dice')
    

