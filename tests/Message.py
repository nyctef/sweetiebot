from modules import Message
import unittest

def create_message(input, is_pm=False):
    return Message('Sweetiebot', 'sender', 'chat@jabber.org/sender', 'sender@jabber.org', input, input, is_pm)

class MessageParsingTests(unittest.TestCase):

    def test_parse_simple_command(self):
        message = create_message('Sweetiebot: roll some dice')
        self.assertEqual(message.command, 'roll')
        self.assertEqual(message.args, 'some dice')

    def test_parse_non_command(self):
        message = create_message('do a thing')
        self.assertFalse(message.command)
        self.assertFalse(message.args)

    def test_ping(self):
        message = create_message('I think sweetiebot should do a thing')
        self.assertTrue(message.is_ping)
        self.assertFalse(message.command)

    def test_pms_are_always_pings(self):
        message = create_message('here is a pm', is_pm=True)
        self.assertTrue(message.is_ping)

    def test_can_have_comma_before_command(self):
        message = create_message('Sweetiebot, roll some dice')
        self.should_roll_some_dice(message)

    def test_can_have_space_before_command(self):
        message = create_message('Sweetiebot roll some dice')
        self.should_roll_some_dice(message)

    def test_command_can_just_have_prefix(self):
        message = create_message('!roll some dice')
        self.should_roll_some_dice(message)

    def test_command_can_have_nickname_and_colon_and_prefix(self):
        message = create_message('Sweetiebot: !roll some dice')
        self.should_roll_some_dice(message)
    

    def should_roll_some_dice(self, message):
        self.assertEqual(message.command, 'roll')
        self.assertEqual(message.args, 'some dice')
    
