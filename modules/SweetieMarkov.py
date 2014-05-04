from jabberbot import botcmd
from utils import logerrors
import utils
import logging
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
    chattiness = .02
    max_words = 30
    messages_to_generate = 100

    def __init__(self, bot, nickname, redis):
        self.bot = bot
        self.bot.load_commands_from(self)
        self.redis = redis
        self.nickname = nickname

    def store_message(self, message):
        for words in self.split_message(message):
            self.redis.store_chain(words)

    def get_sender_username(self, mess):
        return self.bot.get_sender_username(mess)

    def split_message(self, message):
        # split the incoming message into words, i.e. ['what', 'up', 'bro']
        words = re.findall(r"[\w'-]+|:[\w]:|[.,!?;]", message)
        #print(words)

        # if the message is any shorter, it won't lead anywhere
        if len(words) > self.chain_length:
            # add some stop words onto the message
            # ['what', 'up', 'bro', '\x02']
            words.append(self.redis.stop_word)

            # len(words) == 4, so range(4-2) == range(2) == 0, 1, meaning
            # we return the following slices: [0:3], [1:4]
            # or ['what', 'up', 'bro'], ['up', 'bro', '\x02']
            for i in range(len(words) - self.chain_length):
                yield words[i:i + self.chain_length + 1]

    @logerrors
    def get_message(self, seed):
        messages = []
        for words in self.split_message(seed):
            key = self.redis.make_key(words[:-1])
            best_message = ''
            for i in range(self.messages_to_generate):
                generated = self.get_message_from_key(key)
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
            words = key.split(self.redis.separator)

            # add the word to the list of words in our generated message
            gen_words.append(words[0])

            # get a new word that lives at this key -- if none are present we've
            # reached the end of the chain and can bail
            next_word = self.redis.get_next_word(key)
            if not next_word:
                break

            # create a new key combining the end of the old one and the
            # next_word
            key = self.redis.make_key(words[1:] + [next_word])

        result = ''
        for word in gen_words:
            if word not in ".,!?;": # is not punctuation
                result += ' '
            result += word
        return result.strip()

    def log_mess(self, message):
        say_something = False
        is_ping = utils.is_ping(self.nickname, message)
        if is_ping:
            say_something = True
            print("speaking because pinged..")
        if not say_something:
            say_something = random.random() < self.chattiness
        if say_something:
            print("speaking ..")

            if is_ping:
                logging.warning('fixing ping again?')
                message = self.bot.fix_ping(message)

            return self.get_message(message)

    @botcmd
    def quiet(self, mess, args):
        '''I will only respond to pings'''
        self.chattiness = 0
        sender = self.get_sender_username(mess)
        if 'rainbow' in sender.lower():
            return ':rdderp: okay then'
        if 'luna' in sender.lower():
            return ':lunabeh: fine'
        if 'shard' in sender.lower():
            return "I'll be quiet if you make more emotes for me :sweetiedust:"
        if 'sparkle' in sender.lower():
            return "Yes, my princess :sweetiepleased:"
        if 'spike' in sender.lower():
            return "Oh my! A dragon! :sweetie: Of course I'll be quiet"
        return sender + ': Sorry! I\'ll be quiet'

    @botcmd(name='chat')
    def unquiet(self, mess, args):
        '''I will chat every once in a while'''
        self.chattiness = .025
        return self.get_sender_username(mess) + ': Ok, I\'ll start chatting again'

