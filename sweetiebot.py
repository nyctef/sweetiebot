#!/usr/bin/env python
# coding: utf-8

import redis
import sys
import logging
import psycopg2
from utils import randomstr
from modules import MUCJabberBot, ResponsesFile, SweetieAdmin, \
    SweetieChat, SweetieLookup, FakeRedis, SweetieRoulette, \
    RestartException, SweetieDe, SweetiePings, \
    TwitterClient, SweetieSeen, AtomWatcher, SweetieTell, \
    SweetieDictionary, SweetieMoon, TableList, TellStorageRedis
import time
import os
import traceback
from opencensus.ext.azure.log_exporter import AzureLogHandler

log = logging.getLogger(__name__)

class Sweetiebot(object):
    def __init__(self, nickname, bot, lookup, admin, chat, roulette,
                 sweetiede, pings, watchers, moon):
        self.nickname = nickname
        self.bot = bot
        self.bot.unknown_command_callback = self.unknown_command
        self.lookup = lookup
        self.admin = admin
        self.chat = chat
        self.roulette = roulette
        self.sweetiede = SweetieDe
        self.pings = pings
        self.watchers = watchers
        self.moon = moon
        self.bot.add_recurring_task(self.check_watchers, 5*60)

    def check_watchers(self):
        for w in self.watchers:
            next = w.get_next()
            if next:
                self.bot.send_groupchat_message(next)

    def unknown_command(self, message):
        return self.chat.random_chat(message)

def build_sweetiebot(config=None):
    if config is None: import config
    resource = config.nickname + randomstr()
    if config.fake_redis:
        log.debug('faking out redis')
        redis_conn = FakeRedis()
    else:
        redis_conn = redis.from_url(config.redis_url)
    
    if config.pg_conn_str:
        pg_conn = psycopg2.connect(config.pg_conn_str)
    else:
        raise Exception("pg connection string must be set")

    jid = config.username + '/' + resource
    nick = config.nickname
    room = config.chatroom
    password = config.password
    if config.hostname is not None:
        address = (config.hostname, config.port)
    else:
        address = ()

    bot = MUCJabberBot(jid, password, room, nick, address)
    lookup = SweetieLookup(bot)
    admin = SweetieAdmin(bot, config.chatroom)
    de = SweetieDe(bot, admin, TableList(pg_conn, 'deowl_fails'))
    actions = TableList(pg_conn, 'actions')
    sass = TableList(pg_conn, 'sass')
    cadmusic = TableList(pg_conn, 'cadmusic')
    tell_storage = TellStorageRedis(redis_conn)
    tell = SweetieTell(bot, tell_storage)
    dictionary = SweetieDictionary(bot)
    chat = SweetieChat(bot, actions, sass, config.chatroom, cadmusic, tell, dictionary)
    roulette = SweetieRoulette(bot, admin)
    pings = SweetiePings(bot, redis_conn)
    moon = SweetieMoon(bot)
    if config.twitter_key is not None:
        twitter = TwitterClient.get_client(config.twitter_key, config.twitter_secret)
        watchers = list(map(twitter.get_timeline_watcher, ['EVE_Status']))
    else:
        watchers = []
    watchers.append(AtomWatcher.get_watcher('http://eveion.blogspot.com/feeds/posts/default'))
    seen = SweetieSeen(bot, redis_conn)

    sweet = Sweetiebot(config.nickname, bot, lookup, admin, chat, roulette,
                       de, pings, watchers, moon)
    return sweet

def setup_logging(config):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers = []

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.DEBUG if config.debug else logging.INFO)
    streamhandler.setFormatter(formatter)
    root_logger.addHandler(streamhandler)

    if config.app_insights_key is not None:
        azure_handler = AzureLogHandler(
            instrumentation_key=config.app_insights_key
        )
        azure_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(azure_handler)

    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)
    logging.getLogger('sleekxmpp.plugins.xep_0199.ping').setLevel(logging.WARNING)

if __name__ == '__main__':
    import config
    setup_logging(config)

    config.fake_redis = ('--test' in sys.argv)

    try:
        sweet = build_sweetiebot(config)
        while True: time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        traceback.print_exc()
        sys.exit(1)

