from modules import Message, SweetieLookup
import unittest
from unittest.mock import MagicMock, patch

def create_message(input, is_pm=False):
    return Message('Sweetiebot', 'sender', 'chat@jabber.org/sender', 'sender@jabber.org', input, input, is_pm)

class LookupTests(unittest.TestCase):

    def setUp(self):
        self.bot = MagicMock()
        self.crest = MagicMock()
        self.lookup = SweetieLookup(self.bot, self.crest)

    def test_can_roll_simple_dice(self):
        message = create_message('!roll 1d20')
        response = self.lookup.roll(message)

        self.assertIsNotNone(int(response))

    def test_wants_the_d(self):
        response = self.lookup.roll(create_message('!roll butts'))
        self.assertEqual("Dice need to be specified in the form 2d20", response)

    def test_fails_nicely_with_unrecognised_dice(self):
        response = self.lookup.roll(create_message('!roll 1dbutts'))
        self.assertEqual("Sorry, don't know how to roll 'butts'", response)

    def test_fails_nicely_with_bad_dice_count(self):
        response = self.lookup.roll(create_message('!roll oned20'))
        self.assertEqual("Sorry, don't know how to roll 'one' dice", response)

    def test_can_parse_number_of_successes(self):
        dice_spec = self.lookup.parse_dice('1d6>5')
        self.assertIsNone(dice_spec.error)
        self.assertEqual(6, dice_spec.sides)
        self.assertEqual(5, dice_spec.threshold)

    def test_can_count_number_of_successes(self):
        response = self.lookup.roll(create_message('!roll 1d6>5'))
        self.assertIn(" successes)", response)

    def test_can_parse_sum(self):
        dice_spec = self.lookup.parse_dice('1d6>5=')
        self.assertTrue(dice_spec.show_sum)

    def test_can_show_sum(self):
        response = self.lookup.roll(create_message('!roll 1d6>5='))
        self.assertIn("(sum ", response)

    def test_can_parse_5d5_sum_ge5(self):
        dice_spec = self.lookup.parse_dice('5d5=>5')
        self.assertTrue(dice_spec.show_sum)
        self.assertEqual(5, dice_spec.threshold)

    def rolls(self, *rolls):
        rolls = list(rolls)
        def mock_function(self, dice=1, sides=6):
            result = rolls.pop(0)
            assert(len(result) == dice)
            return result
        return mock_function

    def test_can_mock_out_get_rolls(self):
        with patch.object(SweetieLookup, 'get_rolls', 
                self.rolls([1,2,3], [2, 4, 6])):
            response = self.lookup.roll(create_message('!roll 3d3'))
            self.assertEqual("1, 2, 3", response)
            response = self.lookup.roll(create_message('!roll 3d3'))
            self.assertEqual("2, 4, 6", response)

    def test_can_parse_exploding_dice(self):
        dice_spec = self.lookup.parse_dice('10d6!')
        self.assertTrue(dice_spec.explode)

    def test_dice_can_explode(self):
        """exploding dice means that if a dice is rolled at the max value,
        it is re-rolled and the value of that dice is extended with the 
        new roll value. This can happen multiple times per dice"""
        with patch.object(SweetieLookup, 'get_rolls',
                self.rolls([1, 1, 1, 6, 6, 6], [1, 1, 6], [1], [])):
            response = self.lookup.roll(create_message('!roll 6d6!'))
            self.assertEqual("1, 1, 1, 7, 7, 13", response)

    def test_can_roll_some_shadowrun_dice(self):
        with patch.object(SweetieLookup, 'get_rolls',
                self.rolls([1, 1, 1, 6, 6, 6], [1, 1, 6], [1], [])):
            response = self.lookup.roll(create_message('!roll 6d6!>5='))
            self.assertEqual("1, 1, 1, 7, 7, 13 (3 successes) (sum 30)", response)

