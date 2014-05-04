import random

class FakeRedis(object):
    def __init__(self):
        self.data = {}

    def srandmember(self, key):
        try:
            return random.choice(self.data[key])
        except KeyError:
            return None

    def sadd(self, key, value):
        if key in self.data:
            self.data[key].append(value)
        else:
            self.data[key] = [value]

