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

    def hincryby(self, key, field, increment):
        if not key in self.data:
            self.data[key] = {}
        hash = self.data[key]
        if not field in hash:
            hash[field] = 0
        hash[field] += increment
        #print(key, '=', field, hash[field])

    def hgetall(self, key):
        return self.data[key]

    def exists(self, key):
        return key in self.data

