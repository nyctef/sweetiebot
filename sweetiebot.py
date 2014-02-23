#!/usr/bin/env python
# coding: utf-8


from jabberbot import botcmd
from datetime import datetime
import random
import redis
import sys
import logging
from utils import logerrors, randomstr
from MUCJabberBot import MUCJabberBot
from ResponsesFile import ResponsesFile
from SweetieAdmin import SweetieAdmin
from SweetieRedis import SweetieRedis
from SweetieChat import SweetieChat
from SweetieLookup import SweetieLookup

class Sweetiebot():
    kick_owl_delay = 7200
    last_owl_kick = 0
    admin = None
    chat = None
    chatroom = None

    def __init__(self, nickname='Sweetiebutt', *args, **kwargs):
        self.nickname = nickname
        resource = 'sweetiebutt' + randomstr()
        self.redis_conn = kwargs.pop(
            'redis_conn', None) or redis.Redis('localhost')
        self.bot = MUCJabberBot(nickname, *args, res=resource, **kwargs)
        self.bot.load_commands_from(self)
        self.bot.unknown_command_callback = self.unknown_command
        self.lookup = SweetieLookup(self.bot)

    def join_room(self, room, nick):
        if self.admin is None:
            self.admin = SweetieAdmin(self.bot, room)
        if self.chat is None:
            actions = ResponsesFile('Sweetiebot.actions')
            sass = ResponsesFile('Sweetiebot.sass')
            sredis = SweetieRedis(self.redis_conn)
            self.chat = SweetieChat(self.bot, sredis, actions, sass, room)
        self.chatroom = room
        self.bot.join_room(room, nick)

    def serve_forever(self):
        self.bot.serve_forever()

    def get_sender_username(self, message):
        return self.bot.get_sender_username(message)

    def unknown_command(self, bot, mess, cmd, args):
        return self.chat.random_chat(bot, mess, cmd, args)

    @botcmd
    @logerrors
    def deowl(self, mess, args):
        '''Only kicks :owl, long cooldown'''
        if self.last_owl_kick:
            if (datetime.now() - self.last_owl_kick).seconds < self.kick_owl_delay:
                return "I'm tired. Maybe another time?"
        print "trying to kick owl ..."
        self.bot.kick(self.chatroom, ':owl', reason=':sweetiestare:')
        self.last_owl_kick = datetime.now()
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

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='sweetiebot.log', level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())

    #username = 'blighted@friendshipismagicsquad.com/sweetiebutt'
    username = 'sweetiebutt@friendshipismagicsquad.com/sweetiebutt'
    #username = 'nyctef@friendshipismagicsquad.com'
    password = open('password.txt', 'r').read().strip()
    chatroom = 'general@conference.friendshipismagicsquad.com'
    nickname = 'Sweetiebot'
    debug = False

    if '--test' in sys.argv:
        chatroom = 'sweetiebot_playground@conference.friendshipismagicsquad.com'
        debug = True
        sweet = Sweetiebot(
            nickname, username, password, redis_conn=FakeRedis(),
            only_direct=False, command_prefix='', debug=True)
    else:
        sweet = Sweetiebot(nickname, username, password,
                           only_direct=False, command_prefix='')

    print sweet.nickname + ' established!'
    print username
    print 'Joining Room:' + chatroom
    sweet.join_room(chatroom, sweet.nickname)
    print 'Joined!'
    sweet.serve_forever()
