from modules import Message
from modules.RoomMember import RoomMember, RoomMemberList
import unittest

def create_message(input, is_pm=False):
    room_members = [
            RoomMember('Sweetiebot', 'sweetiebot@jabber.org/asdf', 'owner', 'moderator'),
            RoomMember('test_user', 'testuser@jabber.org/asdf', 'none', 'participant'),
            RoomMember('sender', 'chat@jabber.org/sender', 'none', 'participant'),
            RoomMember('name with spaces', 'spacename@jabber.org/sender', 'none', 'participant'),
        ]
    room_member_list = RoomMemberList(room_members)
    return Message('Sweetiebot', 'sender', 'chat@jabber.org/sender', 'sender@jabber.org', input, input, is_pm, room_member_list)

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

    def test_commands_are_case_insensitive(self):
        message = create_message('Sweetiebot: rOlL some dice')
        self.should_roll_some_dice(message)

    def should_roll_some_dice(self, message):
        self.assertEqual(message.command, 'roll')
        self.assertEqual(message.args, 'some dice')

    def test_sender_can_not_do_admin_things(self):
        message = create_message('!kick someone')
        self.assertFalse(message.sender_can_do_admin_things())

    def test_nickreason_is_None_for_no_args(self):
        message = create_message('!quote')
        self.assertIsNone(message.nick_reason)
    
    def test_nickreason_parses_single_word_nicks(self):
        message = create_message('!kick someone')
        self.assertEqual(message.nick_reason, ('someone', ''))

    def test_nickreason_parses_single_word_nicks_with_messages(self):
        message = create_message('!kick someone for reasons')
        self.assertEqual(message.nick_reason, ('someone', 'for reasons'))

    def test_nickreason_parses_multi_word_nicks_with_double_quotes(self):
        message = create_message('!kick "a person" for reasons')
        self.assertEqual(message.nick_reason, ('a person', 'for reasons'))

    def test_nickreason_parses_multi_word_nicks_with_single_quotes(self):
        message = create_message("!kick 'a person' for reasons")
        self.assertEqual(message.nick_reason, ('a person', 'for reasons'))

    def test_nickreason_parses_unquoted_multi_word_nicks_if_known(self):
        # 'name with spaces' is in the known member list, so we should count that
        message = create_message("!kick name with spaces for reasons")
        self.assertEqual(message.nick_reason, ('name with spaces', 'for reasons'))

    def test_nickreason_parses_unquoted_multi_word_nicks_if_known_ci(self):
        # as above, but case-insensitive
        message = create_message("!kick NAME WITH SPACES for reasons")
        self.assertEqual(message.nick_reason, ('name with spaces', 'for reasons'))

    def test_nickreason_parses_single_word_nicks_ci(self):
        # as above, but case-insensitive
        message = create_message("!kick TEST_USER for reasons")
        self.assertEqual(message.nick_reason, ('test_user', 'for reasons'))

    def test_nickreason_parses_multi_word_nicks_ci(self):
        # as above, but case-insensitive
        message = create_message("!kick 'NAME WITH SPACES' for reasons")
        self.assertEqual(message.nick_reason, ('name with spaces', 'for reasons'))

    def test_nickreason_parses_multiple_lines(self):
        message = create_message("!tell someone this is\na message")
        self.assertEqual(message.nick_reason, ('someone', 'this is\na message'))
