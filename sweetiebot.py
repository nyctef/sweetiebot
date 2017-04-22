#!/usr/bin/env python
# coding: utf-8

import redis
import sys
import logging
from utils import randomstr
#from time import sleep
from modules import MUCJabberBot, ResponsesFile, SweetieAdmin, \
    SweetieChat, SweetieLookup, SweetieMQ, FakeRedis, SweetieRoulette, \
    RestartException, SweetieMarkov, PBLogHandler, SweetieDe, SweetiePings, \
    TwitterClient, SweetieSeen, AtomWatcher, SweetieTell, SweetieCrest, \
    SweetieDictionary
import time
import os
import traceback

log = logging.getLogger(__name__)

class Sweetiebot(object):
    def __init__(self, nickname, bot, lookup, mq, admin, chat, roulette,
                 sweetiede, pings, watchers):
        self.nickname = nickname
        self.bot = bot
        self.bot.unknown_command_callback = self.unknown_command
        self.lookup = lookup
        self.mq = mq
        self.admin = admin
        self.chat = chat
        self.roulette = roulette
        self.sweetiede = SweetieDe
        self.pings = pings
        self.watchers = watchers
        self.bot.add_recurring_task(self.check_watchers, 5*60)

    def check_watchers(self):
        for w in self.watchers:
            next = w.get_next()
            if next:
                self.bot.send_groupchat_message(next)

    def unknown_command(self, message):
        return self.chat.random_chat(message)

    def disconnect(self):
        self.bot.disconnect()

def build_sweetiebot(config=None):
    if config is None: import config
    resource = config.nickname + randomstr()
    if config.fake_redis:
        log.debug('faking out redis')
        redis_conn = FakeRedis()
    else:
        redis_conn = redis.from_url(config.redis_url)

    jid = config.username + '/' + resource
    nick = config.nickname
    room = config.chatroom
    password = config.password

    bot = MUCJabberBot(jid, password, room, nick)
    crest = SweetieCrest(config.crest_base_url, config.crest_client_id, config.crest_client_secret, config.crest_refresh_token)
    lookup = SweetieLookup(bot, crest)
    admin = SweetieAdmin(bot, config.chatroom)
    mq = SweetieMQ(config)
    de = SweetieDe(bot, admin, mq, ResponsesFile('data/deowl_fails.txt'))
    actions = ResponsesFile('data/actions.txt')
    sass = ResponsesFile('data/sass.txt')
    cadmusic = ResponsesFile('data/cadmusic.txt')
    markov = SweetieMarkov(redis_conn, 'data/banned_keywords.txt',
                           'data/preferred_keywords.txt',
                           'data/swap_words.txt')
    tell = SweetieTell(bot, redis_conn)
    dictionary = SweetieDictionary(bot)
    chat = SweetieChat(bot, actions, sass, config.chatroom, markov, cadmusic, tell, dictionary)
    roulette = SweetieRoulette(bot, admin)
    pings = SweetiePings(bot, redis_conn)
    if hasattr(config, 'twitter_key'):
        twitter = TwitterClient.get_client(config.twitter_key, config.twitter_secret)
        watchers = list(map(twitter.get_timeline_watcher, ['EVE_Status', 'EVEOnline']))
    else:
        watchers = []
    watchers.append(AtomWatcher.get_watcher('http://eveion.blogspot.com/feeds/posts/default'))
    seen = SweetieSeen(bot, redis_conn)

    sweet = Sweetiebot(config.nickname, bot, lookup, mq, admin, chat, roulette,
                       de, pings, watchers)
    return sweet

def setup_logging(config):
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().handlers = []

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.DEBUG if config.debug else logging.INFO)
    streamhandler.setFormatter(formatter)
    logging.getLogger().addHandler(streamhandler)

    filehandler = logging.FileHandler('sweetiebot.log')
    filehandler.setLevel(logging.DEBUG)
    filehandler.setFormatter(formatter)
    logging.getLogger().addHandler(filehandler)

    errorhandler = PBLogHandler(config)
    errorhandler.setLevel(logging.ERROR)
    errorhandler.setFormatter(formatter)
    logging.getLogger().addHandler(errorhandler)

    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)

if __name__ == '__main__':
    import config
    setup_logging(config)
    if '--test' in sys.argv:
        config.fake_redis = True
        config.chatroom = config.test_chatroom
    else:
        config.fake_redis = False

    while True:
        try:
            sweet = build_sweetiebot(config)
            while True: time.sleep(1)
        except RestartException:
            continue
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception:
            traceback.print_exc()
            sys.exit(1)
        finally:
            if sweet is not None: sweet.disconnect()
        break

