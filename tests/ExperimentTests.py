import unittest
from pprint import pprint, pformat
import logging
import laboratory
import types

from modules import make_experiment_object


class TestClassA:
    def api_method_1(self):
        return 1

    def api_method_2(self, num):
        return num


class CandidateClass:
    def api_method_1(self):
        return 1

    # def api_method_2(self, x):
    #     return 24

    def other_method_2(self):
        return "unrelated"


class ExperimentTests(unittest.TestCase):
    def test_foo(self):
        testObj = TestClassA()
        candidateObj = CandidateClass()
        result = make_experiment_object(testObj, candidateObj)

        # no real assertions here, just looking at the logging output when playing around with implementations
        result.api_method_1()
        result.api_method_2(24)
