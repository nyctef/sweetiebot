from datetime import datetime
import urllib.request, urllib.parse, urllib.error
import requests
import logging
import difflib
import json
import random
import re
from xml.etree import ElementTree as ET
from utils import logerrors, botcmd
from random import randint
from modules.MessageResponse import MessageResponse

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
        res = requests.get('http://tumblraas.azurewebsites.net/', timeout=10)
        return res.text.strip()

    @botcmd
    @logerrors
    def rant(self, message):
        '''Rant for a while, courtesy of lokaltog.github.io/tumblr-argument-generator'''
        res = requests.get(
            'http://tumblraas.azurewebsites.net/rant', timeout=10)
        return res.text.strip()

    def get_prices(self, id, system):
        url = "http://api.eve-central.com/api/marketstat?usesystem=" + \
              str(system) + \
              "&typeid=" + \
              str(id)
        log.debug('asking for prices at '+url)
        apiresult = urllib.request.urlopen(url).read()
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
        id_dic = {}

        with open('data/typeid.txt', 'rb') as f:
            for line in f:
                try:
                    line = line.decode('utf-8').replace("\n", "")
                    typeid, item_name = line.split('=', 1)
                    id_dic[item_name.upper()] = int(typeid)
                except Exception as e:
                    log.warning('failed to decode line: (skipping) '+str(e))
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

        url = 'http://gdata.youtube.com/feeds/api/videos?max-results=1&alt=json&safeSearch=none'
        url += '&q={}'.format(keyword)
        if (channel):
            url += '&author={}'.format(channel)
        log.debug('requesting {}'.format(url))

        response = self.get(url, {'GData-Version': '2'})
        if response is None:
            return "Request failed. Something's fucky ..."
        log.debug(response)

        result = json.loads(response)
        entries = result['feed']['entry']
        if not entries: return "No results found, sorry"
        entry = entries[0]
        log.debug('entry found: '+str(entry))
        title = entry['title']['$t']
        links = entry['link']
        links = filter(lambda x: x['rel'] == 'alternate', links)
        links = map(lambda x: x['href'], links)
        link = next(links)

        return title + ' - ' + link

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
        '''[item name] Look up prices in jita'''
        id, name = self.id_lookup(message.args)
        if id is None:
            return 'Couldn\'t find any matches'
        reply = self.get_prices(id, 30000142)
        reply = message.sender_nick + ': '+name.title() + ' - ' + reply
        return reply

    @botcmd
    def roll(self, message):
        '''[eg 5d20] Roll some dice'''
        brup = message.args.split(' ')
        reply = ''
        for args in brup:
            try:
                dice, sides = list(map(int, args.split('d', 1)))
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

    @logerrors
    def random_reddit_link(self, subreddit, domain_filter=None):
        luna_data = self.get('http://www.reddit.com/r/{}/new.json?limit=100'
                .format(subreddit))
        if luna_data is None: raise Exception('failed to call reddit api')
        link_data = self.get_children_of_type(json.loads(luna_data), 't3')
        if domain_filter:
            link_data = list(filter(
                lambda x: x['data']['domain'] in domain_filter,
                link_data))
        log.info('choosing one of {} links'.format(len(link_data)))
        choice = random.choice(link_data)
        link = choice['data']['url']
        text = choice['data']['title']
        html = '<a href="{}">{}</a>'.format(link, text)
        plain = '{} [{}]'.format(text, link)
        return MessageResponse(plain, None, html=html)

    @botcmd
    @logerrors
    def ferret(self, message):
        return self.random_reddit_link('ferret', ('imgur.com', 'i.imgur.com'))

    @botcmd
    @logerrors
    def woon(self, message):
        '''loona woona'''
        luna_data = self.get('http://www.reddit.com/r/luna/new.json?limit=100')
        if luna_data is None: raise Exception('failed to call reddit api')
        link_data = self.get_children_of_type(json.loads(luna_data), 't3')

        kyuu_data = self.get('http://www.reddit.com/user/kyuuketsuki.json?limit=100')
        if kyuu_data is None: raise Exception('failed to call reddit api')
        link_title_data = self.get_children_of_type(json.loads(kyuu_data), 't1')

        log.info('choosing one of {} links'.format(len(link_data)))
        log.info('choosing one of {} comments'.format(len(link_title_data)))
        link = random.choice(link_data)['data']['url']
        text = random.choice(link_title_data)['data']['body']
        text = re.split('\.|!|\?', text)[0]
        html = '<a href="{}">{}</a>'.format(link, text)
        plain = '{} [{}]'.format(text, link)
        return MessageResponse(plain, None, html=html)

    def get_children_of_type(self, reddit_data, kind):
        if type(reddit_data) is dict:
            return self.get_children_from_listing(reddit_data, kind)

        result = []
        for listing in reddit_data:
            for child in self.get_children_from_listing(listing, kind):
                result.append(child)
        return result

    def get_children_from_listing(self, listing_data, kind):
        result = []
        for child in listing_data['data']['children']:
            if child['kind'] == kind:
                result.append(child)
        return result

    def get(self, url, extra_headers={}):
        try:
            headers = {
                    'user-agent': 'sweetiebot',
                    'cache-control': 'no-cache'
            }
            headers.update(extra_headers)
            log.debug('requesting {} with headers {}'.format(url, str(headers)))
            res = requests.get(url, timeout=10, headers=headers)
            return res.text
        except Exception as e:
            log.warning("error fetching url "+url+" : "+str(e))
            return None

