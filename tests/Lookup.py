from modules import Message, SweetieLookup
from modules.RoomMember import RoomMember, RoomMemberList
import unittest
from unittest.mock import MagicMock, patch
from typing import Callable


def create_message(input: str, is_pm: bool = False) -> Message:
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
        is_pm,
        room_member_list,
    )


class LookupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bot = MagicMock()
        self.lookup = SweetieLookup(self.bot)

    def test_can_roll_simple_dice(self) -> None:
        message = create_message("!roll 1d20")
        response = self.lookup.roll(message)

        self.assertIsNotNone(int(response))

    def test_wants_the_d(self) -> None:
        response = self.lookup.roll(create_message("!roll butts"))
        self.assertEqual(
            "Dice need to be specified in the form 2d20 [>x] [<x] [!] [=] [+n]",
            response,
        )

    def test_fails_nicely_with_unrecognised_dice(self) -> None:
        response = self.lookup.roll(create_message("!roll 1dbutts"))
        self.assertEqual("Sorry, don't know how to roll 'butts'", response)

    def test_fails_nicely_with_bad_dice_count(self) -> None:
        response = self.lookup.roll(create_message("!roll oned20"))
        self.assertEqual("Sorry, don't know how to roll 'one' dice", response)

    def test_can_parse_number_of_successes(self) -> None:
        dice_spec = self.lookup.parse_dice("1d6>5")
        self.assertIsNone(dice_spec.error)
        self.assertEqual(6, dice_spec.sides)
        self.assertEqual(5, dice_spec.threshold)

    def test_can_count_number_of_successes(self) -> None:
        response = self.lookup.roll(create_message("!roll 1d6>5"))
        self.assertIn(" successes)", response)

    def test_can_parse_sum(self) -> None:
        dice_spec = self.lookup.parse_dice("1d6>5=")
        self.assertTrue(dice_spec.show_sum)

    def test_can_show_sum(self) -> None:
        response = self.lookup.roll(create_message("!roll 1d6>5="))
        self.assertIn("(sum ", response)

    def test_can_parse_5d5_sum_ge5(self) -> None:
        dice_spec = self.lookup.parse_dice("5d5=>5")
        self.assertTrue(dice_spec.show_sum)
        self.assertEqual(5, dice_spec.threshold)

    def test_can_parse_empty_die_count(self) -> None:
        dice_spec = self.lookup.parse_dice("d20")
        self.assertEqual(1, dice_spec.dice)
        self.assertEqual(20, dice_spec.sides)

    def test_can_handle_spaces_in_dice_spec(self) -> None:
        response = self.lookup.roll(create_message("!roll 1d6 > 5"))
        self.assertIn(" successes)", response)

    def test_can_parse_percent_die(self) -> None:
        dice_spec = self.lookup.parse_dice("1d%")
        self.assertEqual(100, dice_spec.sides)

    def test_can_parse_lt_threshold(self) -> None:
        dice_spec = self.lookup.parse_dice("2d20<5")
        self.assertEqual(5, dice_spec.lt_threshold)

    def test_can_parse_two_thresholds(self) -> None:
        dice_spec = self.lookup.parse_dice("2d20<15>10")
        self.assertEqual(15, dice_spec.lt_threshold)
        self.assertEqual(10, dice_spec.threshold)

    def test_can_parse_bonuses(self) -> None:
        self.assertEqual(+5, self.lookup.parse_dice("2d20+5").bonus)
        self.assertEqual(-5, self.lookup.parse_dice("2d20-5").bonus)
        self.assertEqual(+2, self.lookup.parse_dice("2d20-5+7").bonus)

    def test_complains_about_non_overlapping_thresholds(self) -> None:
        response = self.lookup.roll(create_message("!roll 2d10>10<5"))
        self.assertEqual(
            "Requirements unsatisfactory: thresholds conflict. Try again.", response
        )

    def rolls(self, *rolls: list[int]) -> Callable[[SweetieLookup, int, int], list[int]]:
        rolls = list(rolls)

        def mock_function(self: SweetieLookup, dice: int = 1, sides: int = 6) -> list[int]:
            result = rolls.pop(0)
            assert len(result) == dice
            return result

        return mock_function

    def test_can_mock_out_get_rolls(self) -> None:
        with patch.object(SweetieLookup, "get_rolls", self.rolls([1, 2, 3], [2, 4, 6])):
            response = self.lookup.roll(create_message("!roll 3d3"))
            self.assertEqual("1, 2, 3", response)
            response = self.lookup.roll(create_message("!roll 3d3"))
            self.assertEqual("2, 4, 6", response)

    def test_can_add_bonus(self) -> None:
        with patch.object(SweetieLookup, "get_rolls", self.rolls([1, 2, 3])):
            response = self.lookup.roll(create_message("!roll 3d3+10>12"))
            self.assertEqual("11, 12, 13 (2 successes)", response)

    def test_uses_both_thresholds_for_success_checks(self) -> None:
        with patch.object(SweetieLookup, "get_rolls", self.rolls([1, 2, 3])):
            response = self.lookup.roll(create_message("!roll 3d3+10>12<12"))
            self.assertEqual("11, 12, 13 (1 successes)", response)

    def test_can_parse_exploding_dice(self) -> None:
        dice_spec = self.lookup.parse_dice("10d6!")
        self.assertTrue(dice_spec.explode)

    def test_dice_can_explode(self) -> None:
        """exploding dice means that if a dice is rolled at the max value,
        it is re-rolled and the value of that dice is extended with the
        new roll value. This can happen multiple times per dice"""
        with patch.object(
            SweetieLookup,
            "get_rolls",
            self.rolls([1, 1, 1, 6, 6, 6], [1, 1, 6], [1], []),
        ):
            response = self.lookup.roll(create_message("!roll 6d6!"))
            self.assertEqual("1, 1, 1, 7, 7, 13", response)

    def test_can_roll_some_shadowrun_dice(self) -> None:
        with patch.object(
            SweetieLookup,
            "get_rolls",
            self.rolls([1, 1, 1, 6, 6, 6], [1, 1, 6], [1], []),
        ):
            response = self.lookup.roll(create_message("!roll 6d6!>5="))
            self.assertEqual("1, 1, 1, 7, 7, 13 (3 successes) (sum 30)", response)
