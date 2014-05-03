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
    SweetieChat, SweetieLookup, SweetieMQ

class Sweetiebot():
    kick_owl_delay = 7200
    last_owl_kick = 0

    def __init__(self, nickname, bot, lookup, mq, admin, chat):
        self.nickname = nickname
        self.bot = bot
        self.bot.load_commands_from(self)
        self.bot.unknown_command_callback = self.unknown_command
        self.lookup = lookup
        self.mq = mq
        self.admin = admin
        self.chat = chat

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

    #@botcmd
    def bye(self, mess, args):
        '''Makes me restart! Blighties only!'''
        if self.get_sender_username(mess) == 'Blighty':
            self.quit()

    #@botcmd
    def yell(self, mess, args):
        '''Yells at everyone Blighties only!'''
        if self.get_sender_username(mess) == 'Blighty':
            self.broadcast(args, True)

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


def build_sweetiebot(debug=True):
    #username = 'blighted@friendshipismagicsquad.com/sweetiebutt'
    username = 'sweetiebutt@friendshipismagicsquad.com/sweetiebutt'
    #username = 'nyctef@friendshipismagicsquad.com'
    password = open('password.txt', 'r').read().strip()
    chatroom = 'general@conference.friendshipismagicsquad.com'
    nickname = 'Sweetiebot'

    resource = 'sweetiebutt' + randomstr()
    if debug:
        chatroom = 'sweetiebot_playground@conference.friendshipismagicsquad.com'
        redis_conn = FakeRedis()
    else:
        redis_conn = redis.Redis('localhost')

    bot = MUCJabberBot(nickname, username, password, res=resource,
                       only_direct=False, command_prefix='', debug=debug)
    lookup = SweetieLookup(bot)
    admin = SweetieAdmin(bot, chatroom)
    mq = SweetieMQ()
    actions = ResponsesFile('data/Sweetiebot.actions')
    sass = ResponsesFile('data/Sweetiebot.sass')
    sredis = SweetieRedis(redis_conn)
    chat = SweetieChat(bot, sredis, actions, sass, chatroom)

    sweet = Sweetiebot(nickname, bot, lookup, mq, admin, chat)
    return sweet, chatroom

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='sweetiebot.log', level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())

    sweet, chatroom = build_sweetiebot('--test' in sys.argv)

    print sweet.nickname + ' established!'
    print 'Joining Room:' + chatroom
    sweet.join_room(chatroom, sweet.nickname)
    print 'Joined!'
    sweet.serve_forever()
