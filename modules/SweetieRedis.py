class SweetieRedis(object):

    separator = '\x01'
    stop_word = '\x02'
    prefix = 'jab'

    def __init__(self, conn):
        self.redis_conn = conn

    def make_key(self, words):
        return self.separator.join(words)

    def _make_key(self, k):
        # todo rename
        return self.separator.join((self.prefix, k))

    def get_next_word(self, key):
        return self.redis_conn.srandmember(self._make_key(key))

    def store_chain(self, words):
        # grab everything but the last word
        key = self.make_key(words[:-1])
        # add the last word to the set
        self.redis_conn.sadd(self._make_key(key), words[-1])
        return key

