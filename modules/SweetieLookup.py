from jabberbot import botcmd
from datetime import datetime
import urllib
import requests
import logging
import difflib
from xml.etree import ElementTree as ET
from utils import logerrors
from random import randint

class SweetieLookup():

    id_dic = {"": ""}

    def __init__(self, bot):
        self.bot = bot
        self.bot.load_commands_from(self)

    def get_sender_username(self, mess):
        return self.bot.get_sender_username(mess)

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

    def get_prices(self, id, system):
        url = "http://api.eve-central.com/api/marketstat?usesystem=" + \
              str(system) + \
              "&typeid=" + \
              str(id)
        logging.debug('asking for prices at '+url)
        apiresult = urllib.urlopen(url).read()
        try:
            root = ET.parse(apiresult).getroot()
        except:
            return "EveCentral is unhappy: "+apiresult[:200]

        buy = root[0][0][0][2].text  # top buy
        sell = root[0][0][1][3].text  # low sell
        buy = '{0:,}'.format(float(buy))
        sell = '{0:,}'.format(float(sell))
        r = 'buy: ' + buy + ' isk, sell: ' + sell + ' isk'
        return r

    def read_ids(self):
        f = open('data/typeid.txt')
        line = f.readline()
        line = line.replace("\n", "")
        id_dic = {}
        while(len(line) > 0):
            typeid, item_name = line.split('=', 1)
            id_dic[unicode(item_name, 'utf-8').upper()] = int(typeid)
            line = f.readline().replace("\n", "")
        f.close()
        return id_dic

    def id_lookup(self, name):
        ''' Lookup a typeid in typeid.txt

        To generate this file, open a recent sqlite data dump with sqlite3
        and run

        .output typeid.txt

        select typeID || '=' || typeName from invTypes where published = 1;
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
            self.id_dic = self.read_ids()

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
                logging.debug("maybe meant " + str(maybe))
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
    
    @botcmd
    @logerrors
    def jita(self, mess, args):
        '''Looks up Jita Prices, use !jita [ITEM NAME]'''
        id, name = self.id_lookup(args)
        if id is None:
            return 'Couldn\'t find any matches'
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
                logging.error('bad dice')
                return "Error parsing input"
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
        logging.debug("roll result: {}".format(reply))
        return reply

    def roll_prim(self, dice=1, sides=6):
        try:
            return [randint(1, sides) for i in range(dice)]
        except:
            return []

    @botcmd
    def date(self, mess, args):
        '''Returns the current date'''
        reply = datetime.now().strftime('%Y-%m-%d')
        reply = self.get_sender_username(mess) + ': ' + reply
        return reply
