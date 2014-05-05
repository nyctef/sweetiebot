#!/usr/bin/env python
# coding: utf-8

from jabberbot import botcmd
from datetime import datetime
import random
import redis
import sys
import logging
import json
from utils import logerrors, randomstr
from modules import MUCJabberBot, ResponsesFile, SweetieAdmin, \
    SweetieChat, SweetieLookup, SweetieMQ, FakeRedis, SweetieRoulette, \
    RestartException, SweetieMarkov, PBLogHandler
log = logging.getLogger(__name__)

class Sweetiebot(object):
    kick_owl_delay = 7200
    last_owl_kick = 0

    def __init__(self, nickname, bot, lookup, mq, admin, chat, roulette):
        self.nickname = nickname
        self.bot = bot
        self.bot.load_commands_from(self)
        self.bot.unknown_command_callback = self.unknown_command
        self.lookup = lookup
        self.mq = mq
        self.admin = admin
        self.chat = chat
        self.roulette = roulette

    def join_room(self, room, nick):
        self.bot.join_room(room, nick)
        self.chatroom = room

    def serve_forever(self):
        self.bot.serve_forever()

    def get_sender_username(self, message):
        return self.bot.get_sender_username(message)

    def unknown_command(self, bot, mess, cmd, args):
        return self.chat.random_chat(bot, mess, cmd, args)

    @botcmd
    @logerrors
    def deowl(self, mess, args):
        speaker = mess.getFrom()
        timestamp = datetime.utcnow()
        mq_message = {
            'deowl':True,
            'room':speaker.getNode(),
            'server':speaker.getDomain(),
            'speaker': speaker.getResource(),
            'timestamp': timestamp.isoformat(' ')
            }
        '''Only kicks :owl, long cooldown'''
        if self.last_owl_kick:
            if (datetime.now() - self.last_owl_kick).seconds < self.kick_owl_delay:
                mq_message['success'] = False
                self.mq.send(json.dumps(mq_message))
                return "I'm tired. Maybe another time?"
        log.debug("trying to kick owl ...")
        self.admin.kick(':owl', ':sweetiestare:')
        self.last_owl_kick = datetime.now()
        self.kick_owl_delay = random.gauss(2*60*60, 20*60)
        mq_message['success'] = True
        self.mq.send(json.dumps(mq_message))
        return

    @botcmd
    def deoctavia(self, mess, args):
        self.detavi(mess, args)

    @botcmd
    @logerrors
    def detavi(self, mess, args):
        speaker = mess.getFrom().getResource()
        log.debug("trying to kick "+speaker)
        target = 'Octavia' if self.admin.nick_is_mod(speaker) else speaker
        self.admin.kick(target, ':lyraahem:')
        return


def build_sweetiebot(config=None):
    if config is None: import config
    resource = config.nickname + randomstr()
    if config.fake_redis:
        redis_conn = FakeRedis()
    else:
        redis_conn = redis.Redis('localhost')

    bot = MUCJabberBot(config.nickname, config.username, config.password, res=resource,
                       only_direct=False, command_prefix='', debug=config.debug)
    lookup = SweetieLookup(bot)
    admin = SweetieAdmin(bot, config.chatroom, config.mods)
    mq = SweetieMQ(config)
    actions = ResponsesFile('data/Sweetiebot.actions')
    sass = ResponsesFile('data/Sweetiebot.sass')
    markov = SweetieMarkov(bot, config.nickname, redis_conn)
    chat = SweetieChat(bot, actions, sass, config.chatroom, markov)
    roulette = SweetieRoulette(bot, admin)

    sweet = Sweetiebot(config.nickname, bot, lookup, mq, admin, chat, roulette)
    return sweet

def setup_logging(config):
    logging.getLogger().setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.INFO)
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

if __name__ == '__main__':
    import config
    setup_logging(config)
    if '--test' in sys.argv:
        config.fake_redis = True
        config.chatroom = config.test_chatroom
    else:
        config.fake_redis = False

    while True:
        sweet = build_sweetiebot(config)

        log.info(sweet.nickname + ' established!')
        log.info('Joining Room:' + config.chatroom)
        sweet.join_room(config.chatroom, sweet.nickname)
        log.info('Joined!')
        try:
            result = sweet.serve_forever()
        except RestartException:
            continue
        break
