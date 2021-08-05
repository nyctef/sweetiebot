import unittest
from unittest.mock import MagicMock, patch
from modules.SweetieChat import SweetieChat

class LinkParsingTests(unittest.TestCase):
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

    def test_can_fetch_youtube_link(self):
        result = self.chat.get_page_titles('this is an interesting video: https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        self.assertEqual('Rick Astley - Never Gonna Give You Up (Official Music Video) by Rick Astley', result)
    
    def test_can_fetch_twitter_link(self):
        result = self.chat.get_page_titles(' https://twitter.com/Graham_LRR/status/1354129384509038593 ')
        self.assertEqual('I don’t know how to make jokes that aren’t about Now any more https://t.co/VvhgGkKPqj — Graham Stark (@Graham_LRR) January 26, 2021 ', result)