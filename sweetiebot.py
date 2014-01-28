#!/usr/bin/env python
# coding: utf-8


from jabberbot import botcmd
from datetime import datetime
import re
import urllib
import xmpp
from xml.etree import ElementTree as ET
import random
from random import randint
import difflib
import redis
import sys
import logging
import requests
from utils import logerrors, randomstr
import utils
from MUCJabberBot import MUCJabberBot
from ResponsesFile import ResponsesFile
from SweetieAdmin import SweetieAdmin
from SweetieRedis import SweetieRedis
from SweetieChat import SweetieChat

class Sweetiebot():
    kick_owl_delay = 7200
    last_owl_kick = 0


    def __init__(self, nickname='Sweetiebutt', *args, **kwargs):
        actions = ResponsesFile('Sweetiebot.actions')
        sass = ResponsesFile('Sweetiebot.sass')
        self.nickname = nickname
        resource = 'sweetiebutt' + randomstr()
        redis_conn = kwargs.pop(
            'redis_conn', None) or redis.Redis('localhost')
        self.bot = MUCJabberBot(nickname, *args, res=resource, **kwargs)
        self.bot.load_commands_from(self)
        self.admin = SweetieAdmin(self.bot, chatroom)
        self.bot.unknown_command_callback = self.unknown_command
        redis = SweetieRedis(redis_conn)
        self.chat = SweetieChat(self.bot, redis, actions, sass)

    def join_room(self, room, nick):
        self.bot.join_room(room, nick)

    def serve_forever(self):
        self.bot.serve_forever()

    def get_sender_username(self, message):
        return self.bot.get_sender_username(message)

    def on_ping_timeout(self):
        print("PING TIMEOUT")
        logging.info('WARNING: ping timeout.')
        # self.quit(1)

    @botcmd
    @logerrors
    def argue(self, message, args):
        '''Start a tumblr argument courtesy of lokaltog.github.io/tumblr-argument-generator'''
        res = requests.get('http://tumblraas.azurewebsites.net/', timeout=5)
        return res.text.strip()

    @botcmd
    @logerrors
    def rant(self, message, args):
        '''Rant for a while, courtesy of lokaltog.github.io/tumblr-argument-generator'''
        res = requests.get(
            'http://tumblraas.azurewebsites.net/rant', timeout=5)
        return res.text.strip()

    def unknown_command(self, bot, mess, cmd, args):
        return self.chat.random_chat(bot, mess, cmd, args)

    def get_prices(self, id, system):
        url = "http://api.eve-central.com/api/marketstat?usesystem=" + \
              str(system) + \
              "&typeid=" + \
              str(id)
        logging.debug('asking for prices at '+url)
        root = ET.parse(urllib.urlopen(url)).getroot()

        buy = root[0][0][0][2].text  # top buy
        sell = root[0][0][1][3].text  # low sell
        buy = '{0:,}'.format(float(buy))
        sell = '{0:,}'.format(float(sell))
        r = 'buy: ' + buy + ' isk, sell: ' + sell + ' isk'
        return r

    def id_lookup(self, name):
        ''' Lookup a typeid in typeid.txt

        To generate this file, open a recent sqlite data dump with sqlite3
        and run

        .output typeid.txt

        select typeID || '=' || typeName from invTypes;
        '''
        if name.lower() == 'plex' or name.lower() == '30 day':
            return 29668, name
        test = name
        test = test.upper()
        test = test.encode('utf-8')
        reply = None
        i_id = None
        i_name = None
        if len(self.id_dic) <= 1:
            f = open('typeid.txt')
            line = f.readline()
            line = line.replace("\n", "")
            while(len(line) > 0):
                typeid, item_name = line.split('=', 1)
                self.id_dic[unicode(item_name, 'utf-8').upper()] = int(typeid)
                line = f.readline().replace("\n", "")
            f.close()

        logging.debug('looking for '+test+' in id_dic')
        if test in list(self.id_dic.keys()):
            logging.debug('.. found')
            reply = self.id_dic[test]
            logging.debug(' .. sending '+test+', '+str(reply))
            return reply, test
        else:
            maybe = difflib.get_close_matches(
                test, list(self.id_dic.keys()), 1)
            if len(maybe) > 0:
                logging.debug("maybe meant " + maybe[0])
                if maybe[0] in list(self.id_dic.keys()):
                    i_id = self.id_dic[maybe[0]]
                    i_name = maybe[0]
        return i_id, i_name

    def youtube_search(self, keyword, channel):
        import gdata.youtube
        import gdata.youtube.service

        client = gdata.youtube.service.YouTubeService()
        query = gdata.youtube.service.YouTubeVideoQuery()

        query.vq = keyword
        query.max_results = 1
        query.start_index = 1
        query.racy = 'include'
        query.orderby = 'relevance'
        if (channel):
            query.author = channel
        feed = client.YouTubeQuery(query)

        for result in feed.entry:
            return result.title.text + ' - ' + result.GetHtmlLink().href
        return "No results found, sorry"

    @botcmd
    @logerrors
    def nerd3(self, mess, args):
        '''Search for a video by NerdCubed'''
        return self.youtube_search(args, 'OfficialNerdCubed')

    @botcmd
    @logerrors
    def tb(self, mess, args):
        '''Search for a video by TotalBiscuit'''
        return self.youtube_search(args, 'TotalHalibut')

    @botcmd
    @logerrors
    def yt(self, mess, args):
        '''Search for a video on youtube'''
        return self.youtube_search(args, None)

    @botcmd
    @logerrors
    def deowl(self, mess, args):
        '''Only kicks :owl, long cooldown'''
        if self.last_owl_kick:
            if (datetime.now() - self.last_owl_kick).seconds < self.kick_owl_delay:
                return "I'm tired. Maybe another time?"
        print "trying to kick owl ..."
        self.bot.kick('general@conference.friendshipismagicsquad.com',
                  ':owl', reason=':sweetiestare:')
        self.last_owl_kick = datetime.now()
        return

    #@botcmd
    @logerrors
    def hype(self, mess, args):
        """Get hype! Print time until S4 starts"""
        # print 'getting hype ..'
        hypetime = datetime.strptime('03:00PM 2013-11-23', '%I:%M%p %Y-%m-%d')
        now = datetime.now()
        diff = hypetime - now
        message = 'GET HYPE! ONLY {0} DAYS, {1} HOURS, {2} MINUTES AND {3} SECONDS UNTIL SEASON FOUR!'\
            .format(diff.days, diff.seconds // 3600, (diff.seconds//60) % 60, diff.seconds % 60)
        # print message
        return message

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

    def karan(self, mess, args):
        '''Looks up Karan Prices, use !karan [ITEM NAME]'''
        id, name = self.id_lookup(args)
        if id is None:
            return ''
        reply = self.get_prices(id, 30004306)
        reply = reply = self.get_sender_username(
            mess) + ': '+name.title() + ' - ' + reply
        return reply

    @botcmd
    @logerrors
    def jita(self, mess, args):
        '''Looks up Jita Prices, use !jita [ITEM NAME]'''
        id, name = self.id_lookup(args)
        if id is None:
            return ''
        reply = self.get_prices(id, 30000142)
        reply = reply = self.get_sender_username(
            mess) + ': '+name.title() + ' - ' + reply
        return reply

    @botcmd
    def roll(self, mess, args):
        '''Accepts rolls in the form of 'roll 1d6' and similar -- max 25 dice'''
        brup = args.split(' ')
        reply = ''
        for args in brup:
            try:
                dice, sides = map(int, args.split('d', 1))
            except:
                return
            if dice > 25:
                return "Too many variables in possibilty space, abort!"
            if sides > 20000000:
                return "Sides of dice too small, can't see what face is upright!"
            if sides == 1:
                return "Oh look, they all came up ones. Are you suprised? I'm suprised."
            if sides < 1:
                return "How do you make a dice with less than two sides?"
            if dice < 1:
                return "You want me to roll...less than one dice?"
            rolls = self.roll_prim(dice, sides)
            if len(rolls) < 1:
                return
            new_dice = ', '.join(map(str, rolls))
            if not reply:
                reply = new_dice
            else:
                reply = reply + " ~ " + new_dice
        return reply

    @botcmd
    def date(self, mess, args):
        '''Returns the current date'''
        reply = datetime.now().strftime('%Y-%m-%d')
        reply = self.get_sender_username(mess) + ': ' + reply
        return reply

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
