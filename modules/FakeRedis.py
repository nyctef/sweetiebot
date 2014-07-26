import random
from fnmatch import fnmatch

class FakeRedis(object):
    def __init__(self):
        self.data = {}

    def keys(self, pattern):
        return [x for x in list(self.data.keys()) if fnmatch(x, pattern)]

    def srandmember(self, key):
        try:
            return random.choice(self.data[key])
        except KeyError:
            return None

    def sadd(self, key, value):
        if key in self.data:
            if value in self.data[key]:
                return 0
            self.data[key].append(value)
            return 1
        self.data[key] = [value]
        return 1

    def smembers(self, key):
        if key in self.data:
            return self.data[key]
        return []

    def srem(self, key, value):
        if key in self.data:
            if value in self.data[key]:
                self.data[key].remove(value)
                return 1

    def scard(self, key):
        return len(self.data[key])

    def hincrby(self, key, field, increment):
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

