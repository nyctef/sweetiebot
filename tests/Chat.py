from modules import Message, SweetieChat
from modules.RoomMember import RoomMember, RoomMemberList
import unittest
from unittest.mock import MagicMock, patch
from pprint import pprint


def create_message(input, is_pm=False):
    room_members = [
        RoomMember("Sweetiebot", "sweetiebot@jabber.org/asdf", "owner", "moderator"),
        RoomMember("test_user", "testuser@jabber.org/asdf", "none", "participant"),
        RoomMember("sender", "chat@jabber.org/sender", "none", "participant"),
    ]
    room_member_list = RoomMemberList(room_members)
    return Message(
        "Sweetiebot",
        "sender",
        "chat@jabber.org/sender",
        "sender@jabber.org",
        input,
        input,
        is_pm,
        room_member_list,
    )


class SweetieChatTests(unittest.TestCase):
    def setUp(self):
        self.bot = MagicMock()
        self.actions = MagicMock()
        self.sass = MagicMock()
        self.sass.get_next = MagicMock(name="some sass")
        self.chatroom = MagicMock()
        self.cadmusic = MagicMock()
        self.tell = MagicMock()
        self.tell.get_messages_for = MagicMock(return_value=None)
        self.dictionary = MagicMock()
        self.dictionary.get_definition = MagicMock(return_value="a picture of you")

        self.chat = SweetieChat(
            self.bot,
            self.actions,
            self.sass,
            self.chatroom,
            self.cadmusic,
            self.tell,
            self.dictionary,
        )

    def test_can_choose_a_thing(self):
        response = self.chat.choose(create_message("!choose pizza,pie,calzone"))
        self.assertIn(response, ["pizza", "pie", "calzone"])

    def test_does_not_show_permission_failed_title(self):
        return  # this test is a bit slow
        response = self.chat.random_chat(
            create_message("https://forum.pleaseignore.com/topic/83206/")
        )
        self.assertIsNone(response)

    def test_does_not_cd_in_middle_of_word(self):
        response = self.chat.random_chat(
            create_message("you're a medic/doctor, right?")
        )
        self.assertIsNone(response)

    def test_sweetiebot_yes(self):
        response = self.chat.random_chat(create_message("Sweetiebot no"))
        self.assertEqual("Sweetiebot yes! :sweetieglee:", response)

    def test_how_x_is_y(self):
        response = self.chat.random_chat(create_message("Sweetiebot: how x is y?"))
        self.assertEqual("sender: y [74.06% x]", response)
        response2 = self.chat.random_chat(create_message("Sweetiebot: how blue is red"))
        self.assertEqual("sender: red [51.89% blue]", response2)
        response3 = self.chat.random_chat(
            create_message("Sweetiebot: how amazing are amazing people")
        )
        self.assertEqual("sender: amazing people [13.67% amazing]", response3)
        response4 = self.chat.random_chat(
            create_message("Sweetiebot: how totally silly are silly people")
        )
        self.assertEqual("sender: silly people [11.49% totally silly]", response4)

    def test_misc(self):
        print(self.chat.random_chat(create_message("Sweetiebot: how do you do?")))
        print(
            self.chat.random_chat(
                create_message("Sweetiebot: how do you want to play this?")
            )
        )
        print(self.chat.random_chat(create_message("Sweetiebot: what is love?")))
        print(
            self.chat.random_chat(create_message("Sweetiebot: will she ever love me"))
        )

    def test_dictionary(self):
        response = self.chat.random_chat(
            create_message("Sweetiebot: what is an idiot?")
        )
        self.assertEqual("a picture of you", response)

    def test_mlyp(self):
        response = self.chat.random_chat(create_message("Freddy Mercury is gay"))
        self.assertEqual("sender: mlyp", response)
