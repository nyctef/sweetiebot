from utils import logerrors
import re
import random

class SweetieMarkov(object):

    preferred_endings = ['.', '~', '!']
    banned_endings = [ 'and', 'or', 'aboard', 'about', 'above', 'across',
                      'after', 'against', 'along', 'amid', 'among', 'anti',
                      'around', 'as', 'at', 'before', 'behind', 'below',
                      'beneath', 'beside', 'besides', 'between', 'beyond',
                      'but', 'by', 'concerning', 'considering', 'despite',
                      'down', 'during', 'except', 'excepting', 'excluding',
                      'following', 'for', 'from', 'in', 'inside', 'into',
                      'like', 'minus', 'near', 'of', 'off', 'on', 'onto',
                      'opposite', 'outside', 'over', 'past', 'per', 'plus',
                      'regarding', 'round', 'save', 'since', 'than', 'through',
                      'to', 'toward', 'towards', 'under', 'underneath',
                      'unlike', 'until', 'up', 'upon', 'versus', 'via', 'with',
                      'within', 'without']

    chain_length = 3
    min_reply_length = 3
    max_words = 30
    messages_to_generate = 100

    separator = '\x01'
    stop_word = '\x02'
    prefix = 'jab'

    def __init__(self, bot, nickname, redis):
        self.bot = bot
        self.redis = redis
        self.nickname = nickname

    def make_key(self, words):
        return self.separator.join(words)

    def _make_key(self, k):
        # todo rename
        return self.separator.join((self.prefix, k))

    def get_next_word(self, key):
        return self.redis.srandmember(self._make_key(key))

    def store_chain(self, words):
        # grab everything but the last word
        key = self.make_key(words[:-1])
        # add the last word to the set
        self.redis.sadd(self._make_key(key), words[-1])
        return key

    def store_message(self, message):
        for words in self.split_message_into_subsequences(message):
            self.store_chain(words)

    def get_sender_username(self, mess):
        return self.bot.get_sender_username(mess)

    def split_message(self, message):
        return re.findall(r"[\w'-]+|:[\w]:|[.,!?;]", message)

    def split_message_into_subsequences(self, message):
        # split the incoming message into words, i.e. ['what', 'up', 'bro']
        words = self.split_message(message)
        #print(words)

        # if the message is any shorter, it won't lead anywhere
        if len(words) > self.chain_length:
            # add some stop words onto the message
            # ['what', 'up', 'bro', '\x02']
            words.append(self.stop_word)

            # len(words) == 4, so range(4-2) == range(2) == 0, 1, meaning
            # we return the following slices: [0:3], [1:4]
            # or ['what', 'up', 'bro'], ['up', 'bro', '\x02']
            for i in range(len(words) - self.chain_length):
                yield words[i:i + self.chain_length + 1]

    def is_subset(self, smaller, larger):
        return set(smaller) <= set(larger)

    def is_submessage(self, generated, original):
        """return if the generated message is just a subset of the input"""
        return self.is_subset(self.split_message(generated),
                              self.split_message(original))

    @logerrors
    def get_message(self, seed):
        messages = []
        for words in self.split_message_into_subsequences(seed):
            key = self.make_key(words[:-1])
            best_message = ''
            for i in range(self.messages_to_generate):
                generated = self.get_message_from_key(key)
                if self.is_submessage(generated, seed):
                    continue
                if generated[-1] in self.preferred_endings:
                    best_message = generated
                    break
                if len(generated) > len(best_message):
                    if not generated.split(' ')[-1] in self.banned_endings:
                        best_message = generated

            if len(best_message.split(' ')) > self.min_reply_length:
                print("Candidate best message " + best_message)
                messages.append(best_message)
            else:
                print("Best message for " + '_'.join(words) + " was " +
                        best_message + ", not long enough")

        if len(messages):
            return random.choice(messages)


    def get_message_from_key(self, key):
        # keep a list of words we've seen
        gen_words = []

        # only follow the chain so far, up to <max words>
        for i in xrange(self.max_words):

            # split the key on the separator to extract the words -- the key
            # might look like "this\x01is" and split out into [ 'this', 'is']
            words = key.split(self.separator)

            # add the word to the list of words in our generated message
            gen_words.append(words[0])

            # get a new word that lives at this key -- if none are present we've
            # reached the end of the chain and can bail
            next_word = self.get_next_word(key)
            if not next_word:
                break

            # create a new key combining the end of the old one and the
            # next_word
            key = self.make_key(words[1:] + [next_word])

        return self.build_message(gen_words)

    def build_message(self, gen_words):
        result = ''
        for word in gen_words:
            if word not in ".,!?;": # is not punctuation
                result += ' '
            result += word
        return result.strip()


