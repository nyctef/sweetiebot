from jabberbot import botcmd
from datetime import datetime
import urllib
import requests
import logging
import difflib
from xml.etree import ElementTree as ET
from utils import logerrors
from random import randint

log = logging.getLogger(__name__)

class SweetieLookup(object):

    id_dic = {"": ""}

    def __init__(self, bot):
        self.bot = bot
        self.bot.load_commands_from(self)

    def get_sender_username(self, mess):
        return self.bot.get_sender_username(mess)

    @botcmd
    @logerrors
    def argue(self, message):
        '''Start a tumblr argument courtesy of lokaltog.github.io/tumblr-argument-generator'''
        res = requests.get('http://tumblraas.azurewebsites.net/', timeout=5)
        return res.text.strip()

    @botcmd
    @logerrors
    def rant(self, message):
        '''Rant for a while, courtesy of lokaltog.github.io/tumblr-argument-generator'''
        res = requests.get(
            'http://tumblraas.azurewebsites.net/rant', timeout=5)
        return res.text.strip()

    def get_prices(self, id, system):
        url = "http://api.eve-central.com/api/marketstat?usesystem=" + \
              str(system) + \
              "&typeid=" + \
              str(id)
        log.debug('asking for prices at '+url)
        apiresult = urllib.urlopen(url).read()
        try:
            root = ET.fromstring(apiresult)
        except:
            log.exception('error parsing evecentral xml')
            return "EveCentral is unhappy: "+apiresult[:200]

        buy = root.find('marketstat/type/buy/max').text
        sell = root.find('marketstat/type/sell/min').text
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
            try:
                id_dic[unicode(item_name, 'utf-8').upper()] = int(typeid)
            except UnicodeDecodeError:
                log.warning('failed to utf-8 decode line: '+typeid+' (skipping)')
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

        log.debug('looking for '+test+' in id_dic')
        if test in list(self.id_dic.keys()):
            log.debug('.. found')
            reply = self.id_dic[test]
            log.debug(' .. sending '+test+', '+str(reply))
            return reply, test
        else:
            maybe = difflib.get_close_matches(
                test, list(self.id_dic.keys()), 1)
            if len(maybe) > 0:
                log.debug("maybe meant " + str(maybe))
                if maybe[0] in list(self.id_dic.keys()):
                    i_id = self.id_dic[maybe[0]]
                    i_name = maybe[0]
        return i_id, i_name

    def youtube_search(self, keyword, channel):
        if not keyword or keyword.isspace():
            return "https://www.youtube.com/watch?v=qRC4Vk6kisY"
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
    def nerd3(self, message):
        '''Search for a video by NerdCubed'''
        return self.youtube_search(message.args, 'OfficialNerdCubed')

    @botcmd
    @logerrors
    def tb(self, message):
        '''Search for a video by TotalBiscuit'''
        return self.youtube_search(message.args, 'TotalHalibut')

    @botcmd
    @logerrors
    def yt(self, message):
        '''Search for a video on youtube'''
        return self.youtube_search(message.args, None)

    @logerrors
    def hype(self, message):
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
    def jita(self, message):
        '''Looks up Jita Prices, use !jita [ITEM NAME]'''
        id, name = self.id_lookup(message.args)
        if id is None:
            return 'Couldn\'t find any matches'
        reply = self.get_prices(id, 30000142)
        reply = message.sender_nick + ': '+name.title() + ' - ' + reply
        return reply

    @botcmd
    def roll(self, message):
        '''Accepts rolls in the form of 'roll 1d6' and similar -- max 25 dice'''
        brup = message.args.split(' ')
        reply = ''
        for args in brup:
            try:
                dice, sides = map(int, args.split('d', 1))
            except:
                log.error('bad dice')
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
        log.debug("roll result: {}".format(reply))
        return reply

    def roll_prim(self, dice=1, sides=6):
        try:
            return [randint(1, sides) for i in range(dice)]
        except:
            return []

    @botcmd
    def date(self, message):
        '''Returns the current date'''
        reply = datetime.now().strftime('%Y-%m-%d')
        reply = message.sender_nick + ': ' + reply
        return reply

