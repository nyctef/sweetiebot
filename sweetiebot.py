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
from modules import MUCJabberBot, ResponsesFile, SweetieAdmin, SweetieRedis,\
    SweetieChat, SweetieLookup, SweetieMQ, FakeRedis, SweetieRoulette, \
    RestartException

class Sweetiebot():
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
        print "trying to kick owl ..."
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
        print "trying to kick "+speaker
        self.admin.kick(speaker, ':lyraahem:')
        return


def build_sweetiebot(config=None):
    if config is None: import config
    resource = config.nickname + randomstr()
    if config.debug:
        redis_conn = FakeRedis()
    else:
        redis_conn = redis.Redis('localhost')

    bot = MUCJabberBot(config.nickname, config.username, config.password, res=resource,
                       only_direct=False, command_prefix='', debug=config.debug)
    lookup = SweetieLookup(bot)
    admin = SweetieAdmin(bot, config.chatroom)
    mq = SweetieMQ(config)
    actions = ResponsesFile('data/Sweetiebot.actions')
    sass = ResponsesFile('data/Sweetiebot.sass')
    sredis = SweetieRedis(redis_conn)
    chat = SweetieChat(bot, sredis, actions, sass, config.chatroom)
    roulette = SweetieRoulette(bot, admin)

    sweet = Sweetiebot(config.nickname, bot, lookup, mq, admin, chat, roulette)
    return sweet

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='sweetiebot.log', level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())

    while True:
        import config
        if '--test' in sys.argv:
            config.debug = True
            config.chatroom = config.test_chatroom
        sweet = build_sweetiebot(config)

        print sweet.nickname + ' established!'
        print 'Joining Room:' + config.chatroom
        sweet.join_room(config.chatroom, sweet.nickname)
        print 'Joined!'
        try:
            result = sweet.serve_forever()
        except RestartException:
            continue
        break
