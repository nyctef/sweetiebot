class SweetieRedis():

    separator = '\x01'
    stop_word = '\x02'
    prefix = 'jab'

    def __init__(self, conn):
        self.redis_conn = conn

    def make_key(self, k):
        return '-'.join((self.prefix, k))

    def get_next_word(self, key):
        self.redis_conn.srandmember(self.make_key(key))

    def store_chain(self, words):
        # grab everything but the last word
        key = self.separator.join(words[:-1])
        # add the last word to the set
        self.redis_conn.sadd(self.make_key(key), words[-1])
        return key

