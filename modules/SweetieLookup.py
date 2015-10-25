from datetime import datetime
import urllib.request, urllib.parse, urllib.error
import requests
from requests.exceptions import Timeout
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
        try:
            apiresult = requests.get(url).text
            root = ET.fromstring(apiresult)
        except Exception as e:
            print(e)
            log.exception(e, 'error parsing evecentral xml')
            return "EveCentral is unhappy: "+apiresult[:200]

        buy = root.find('marketstat/type/buy/max').text
        sell = root.find('marketstat/type/sell/min').text
        buy = '{0:,}'.format(float(buy))
        sell = '{0:,}'.format(float(sell))
        r = 'buy: ' + buy + ' isk, sell: ' + sell + ' isk'
        return r

    def read_ids(self):
        result = {}
        types_href_regex = re.compile('https://public-crest.eveonline.com/types/(\d+)/')
        types_url = 'https://public-crest.eveonline.com/types/'
        while types_url:
            try:
                types_res = requests.get(types_url, timeout=10)
                types = json.loads(types_res.text)
                for type in types['items']:
                    id = types_href_regex.match(type['href']).group(1)
                    name = type['name'].upper()
                    result[name] = id
                if 'next' in types:
                    types_url = types['next']['href']
                else:
                    types_url = None
            except Timeout as t:
                raise
            except Exception as e:
                log.exception(e)
        log.info('found {} typeid results'.format(len(result)))
        return result

    def id_lookup(self, name):
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

    class Bunch:
        __init__ = lambda self, **kw: setattr(self, '__dict__', kw)
        __getattr__ = lambda self, name: None

    def dice_error(self, message, *args):
        return SweetieLookup.Bunch(error=message.format(*args))

    def parse_dice(self, dice):
        split = dice.split('d', 1)
        if len(split) < 2:
            return self.dice_error("Dice need to be specified in the form 2d20")
        dice_count = split[0]
        dice_type = split[1]
        try:
            dice = int(dice_count)
        except:
            return self.dice_error("Sorry, don't know how to roll '{}' dice", dice_count)
        try:
            split_modifiers = re.split(r'(\d+|=|>|!)', dice_type)
            split_modifiers = list(filter(len, split_modifiers))
            sides = int(split_modifiers[0])
            current_modifier = None
            threshold = None
            show_sum = False
            explode = False
            # iterate over dice spec, remembering what the last modifier was 
            # in order to interpret the different numbers
            for modifier in split_modifiers:
                if modifier.isdigit():
                    if current_modifier == '>':
                        threshold = int(modifier)
                        current_modifier = None
                    else: 
                        assert(current_modifier is None)
                        sides = int(modifier)
                elif modifier == '>':
                    current_modifier = modifier
                elif modifier == '=':
                    show_sum = True
                elif modifier == '!':
                    explode = True
                else:
                    raise "unknown modifier"

            return SweetieLookup.Bunch(dice=dice, sides=sides,
                    threshold=threshold, show_sum=show_sum,
                    explode=explode)
        except:
            return self.dice_error("Sorry, don't know how to roll '{}'", dice_type)
        return SweetieLookup.Bunch(dice=dice, sides=sides)

    @botcmd
    def roll(self, message):
        '''[eg 5d20] Roll some dice'''
        brup = message.args.split(' ')
        for args in brup:
            try:
                dice_spec = self.parse_dice(args)
                if dice_spec.error:
                    return dice_spec.error
                dice = dice_spec.dice
                sides = dice_spec.sides
            except Exception as e:
                log.error('bad dice '+str(e))
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
            rolls = self.get_rolls(dice, sides)
            if dice_spec.explode:
                rolls = self.explode_dice(rolls, sides)
        log.debug("roll result: {}".format(rolls))
        roll_list = ', '.join(map(str, rolls))
        if dice_spec.threshold:
            success_count = len(list(filter(lambda x: x >= dice_spec.threshold, rolls)))
            roll_list += " ({} successes)".format(success_count)
        if dice_spec.show_sum:
            dice_sum = sum(rolls)
            roll_list += " (sum {})".format(dice_sum)
        return roll_list

    class ExplodingDice:
        def __init__(self, initialValue):
            self.rolls = [int(initialValue)]
        def last_roll(self):
            return self.rolls[-1]
        def add_roll(self, roll):
            self.rolls.append(int(roll))
            return self
        def sum(self):
            return sum(self.rolls)

    def explode_dice(self, rolls, sides):
        sides = int(sides)
        rolls = list(map(SweetieLookup.ExplodingDice, rolls))
        should_explode = lambda r: r.last_roll() == sides
        add_roll = lambda r, n: r.add_roll(n)
        unexploded_rolls = list(rolls)
        while any(unexploded_rolls):
            unexploded_rolls = list(filter(should_explode, unexploded_rolls))
            rerolls = self.get_rolls(len(unexploded_rolls), sides)
            unexploded_rolls = list(map(add_roll, unexploded_rolls, rerolls))

        return list(map(lambda x: x.sum(), rolls))

    def get_rolls(self, dice=1, sides=6):
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

    @botcmd(hidden=True)
    @logerrors
    def kwote(self, message):
        return self.quote(message)

    @botcmd
    @logerrors
    def quote(self, message):
        '''Cheesy fortune files are the highest form of wit'''
        return "quote is broken while iheartquotes.com is down"
        data = self.get('http://www.iheartquotes.com/api/v1/random?format=json&max_lines=3')
        data = json.loads(data)
        text = data['quote']
        html = text.replace('\n', '<br/>')
        return MessageResponse(text, None, html=html)

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
        plain = '{} [ {} ]'.format(text, link)
        return MessageResponse(plain, None, html=html)

    @botcmd
    @logerrors
    def ferret(self, message):
        '''Ferret!'''
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
        plain = '{} [ {} ]'.format(text, link)
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

