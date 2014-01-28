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

class Sweetiebot():
    kick_owl_delay = 7200
    last_owl_kick = 0
    id_dic = {"": ""}
    id_list = {}
    chain_length = 2
    min_reply_length = 3
    chattiness = .02
    max_words = 30
    messages_to_generate = 100
    lunabeh_top = 10
    lunabeh_count = 0
    prefix = 'jab'
    separator = '\x01'
    stop_word = '\x02'
    target = '<target>'

    urlregex = re.compile(
        r"((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]+|(?:www.|[-;:&=\+\$,\w]+@)[A-Za-z0-9.-]+)((?:\/[\+~%\/.\w_-]*)?\??(?:[-\+=&;%@.\w_]*)#?(?:[\w]*))?)")
    emotes = [':sweetie:', ':sweetiecrack:',
              ':sweetiederp:', ':sweetiedust:',
              ':sweetieglee:', ':sweetieidea:',
              ':sweetiemad:', ':sweetiepleased:',
              ':sweetieoops:', ':sweetieread:',
              ':sweetiescheme:', ':sweetieshake:',
              ':sweetieshrug:', ':sweetiesmug:',
              ':sweetiestare:', ':sweetietwitch:',
              ':egstare:', ':sweetiesiren:']
    preferred_endings = ['.', '~', '!']
    banned_endings = [
        'and', 'or', 'aboard', 'about', 'above', 'across', 'after', 'against', 'along', 'amid', 'among',
        'anti', 'around', 'as', 'at', 'before', 'behind', 'below', 'beneath', 'beside', 'besides',
        'between', 'beyond', 'but', 'by', 'concerning', 'considering', 'despite', 'down', 'during',
        'except', 'excepting', 'excluding', 'following', 'for', 'from', 'in', 'inside', 'into', 'like',
        'minus', 'near', 'of', 'off', 'on', 'onto', 'opposite', 'outside', 'over', 'past', 'per', 'plus',
        'regarding', 'round', 'save', 'since', 'than', 'through', 'to', 'toward', 'towards', 'under',
        'underneath', 'unlike', 'until', 'up', 'upon', 'versus', 'via', 'with', 'within', 'without']

    def __init__(self, nickname='Sweetiebutt', *args, **kwargs):
        self.actions = ResponsesFile('Sweetiebot.actions')
        self.sass = ResponsesFile('Sweetiebot.sass')
        self.nickname = nickname
        resource = 'sweetiebutt' + randomstr()
        redis_conn = kwargs.pop(
            'redis_conn', None) or redis.Redis('localhost')
        self.bot = MUCJabberBot(nickname, *args, res=resource, **kwargs)
        self.bot.load_commands_from(self)
        self.admin = SweetieAdmin(self.bot, chatroom)
        self.redis = SweetieRedis(redis_conn)
        self.bot.unknown_command_callback = self.unknown_command

    def join_room(self, room, nick):
        self.bot.join_room(room, nick)

    def serve_forever(self):
        self.bot.serve_forever()

    def get_sender_username(self, message):
        return self.bot.get_sender_username(message)

    def sanitize_message(self, message):
        if "http" in message:
            return ""
        if "####" in message:
            return ""

        return re.sub('[\"\']', '', message.lower())

    def roll_prim(self, dice=1, sides=6):
        try:
            return [randint(1, sides) for i in range(dice)]
        except:
            return []

    def save_action(self, action_str):
        self.actions.add_to_file(action_str)

    def split_message(self, message):
        # split the incoming message into words, i.e. ['what', 'up', 'bro']
        words = message.split()

        # if the message is any shorter, it won't lead anywhere
        if len(words) > self.chain_length:

            # add some stop words onto the message
            # ['what', 'up', 'bro', '\x02']
            words.append(self.stop_word)

            # len(words) == 4, so range(4-2) == range(2) == 0, 1, meaning
            # we return the following slices: [0:3], [1:4]
            # or ['what', 'up', 'bro'], ['up', 'bro', '\x02']
            for i in range(len(words) - self.chain_length):
                yield words[i:i + self.chain_length + 1]

    @logerrors
    def generate_message(self, seed):
        key = seed

        # keep a list of words we've seen
        gen_words = []

        # only follow the chain so far, up to <max words>
        for i in xrange(self.max_words):

            # split the key on the separator to extract the words -- the key
            # might look like "this\x01is" and split out into [ 'this', 'is']
            words = key.split(self.separator)

            # add the word to the list of words in our generated message
            gen_words.append(words[0])

            # get a new word that lives at this key -- if none are present we've
            # reached the end of the chain and can bail
            next_word = self.redis.get_next_word(key)
            if not next_word:
                break

            # create a new key combining the end of the old one and the
            # next_word
            key = self.separator.join(words[1:] + [next_word])
        return ' '.join(gen_words)

    def cuddle(self, mess):
        logging.debug('cuddle')
        message = mess.getBody().lower()
        if 'pets' in message:
            return '/me purrs ' + random.choice(self.emotes)
        #self.save_action(message.replace('\n',' ')+ '\n')
        action = self.actions.get_next()
        action = action.replace('<target>', self.get_sender_username(mess))
        return action + ' ' + random.choice(self.emotes)

    def log_mess(self, mess, bot):
        # speak only when spoken to, or when the spirit moves me
        jid = mess.getFrom()
        props = mess.getProperties()
        message = mess.getBody()
        message_true = mess.getBody()
        say_something = False
        if xmpp.NS_DELAY in props:
            return
        if not message:
            return
        if self.get_sender_username(mess) == self.nickname:
            return
        if bot.jid.bareMatch(jid):
            return
        if utils.is_ping(self.nickname, message):
            say_something = True
        if not say_something:
            say_something = random.random() < self.chattiness

        messages = []
        # use a convenience method to strip out the "ping" portion of a message
        if utils.is_ping(self.nickname, message):
            logging.warning('fixing ping again?')
            message = bot.fix_ping(message)

        if message_true.startswith('/'):
            if message_true.startswith('/me ') and utils.is_ping(self.nickname, message_true):
                return self.cuddle(mess)
            return

        if say_something:
            print '# ' + self.get_sender_username(mess).encode('utf-8') + ':' + message_true.encode('utf-8')
        else:
            print '  ' + self.get_sender_username(mess).encode('utf-8') + ':' + message_true.encode('utf-8')

        # split up the incoming message into chunks that are 1 word longer than
        # the size of the chain, e.g. ['what', 'up', 'bro'], ['up', 'bro',
        # '\x02']
        for words in self.split_message(self.sanitize_message(message)):
            key = self.redis.store_chain(words)
            # if we should say something, generate some messages based on what
            # was just said and select the longest, then add it to the list
            if say_something:
                best_message = ''
                for i in range(self.messages_to_generate):
                    generated = self.generate_message(seed=key)
                    if generated[-1] in self.preferred_endings:
                        best_message = generated
                        break
                    if len(generated) > len(best_message):
                        if not generated.split(' ')[-1] in self.banned_endings:
                            best_message = generated

                if len(best_message.split(' ')) > self.min_reply_length:
                    print "Candidate best message " + best_message
                    messages.append(best_message)
                else:
                    print "Best message for " + '_'.join(words) + " was " + best_message + ", not long enough"

        if messages:
            final = random.choice(messages)
            try:
                print 'R--> ' + final
            except UnicodeEncodeError:
                print "Error Printing Message..."
            return final
        # If was pinged but couldn't think of something relevant, reply with
        # something generic.
        elif utils.is_ping(self.nickname, message_true):
            print 'Quoting instead...'
            return self.quote(mess, '')

    def on_ping_timeout(self):
        print("PING TIMEOUT")
        logging.info('WARNING: ping timeout.')
        # self.quit(1)

    @logerrors
    def get_page_titles(self, message):
        # hack!
        if 'emotes! http://pastebin' in message.lower():
            return None
        matches = self.urlregex.findall(message)
        matches = map(lambda x: x[0], matches)
        matches = map(self.imgur_filter, matches)
        if matches:
            print("found matches: "+" / ".join(matches))
        results = []
        from bs4 import BeautifulSoup
        for match in matches:
            try:
                res = requests.get(match, timeout=5)
                if not 'html' in res.headers['content-type']:
                    print 'skipping non-html'
                    break
                soup = BeautifulSoup(res.text)
                results.append(soup.title.string)
            except Exception as e:
                print "error fetching url "+match+" : "+str(e)
                pass
        results = filter(self.title_filter, results)
        if not len(results):
            return None
        return " / ".join(results)

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

    def title_filter(self, result):
        if (result.strip() == 'imgur: the simple image sharer'):
            return False
        if (result.strip() == 'Error - Test Forums Please Ignore'):
            return False
        return True

    def imgur_filter(self, link):
        imgurregex = re.compile(r'^http(s)?://i.imgur.com/([a-zA-Z0-9]*)\..*$')
        match = imgurregex.match(link)
        if (match):
            replacement = 'http://imgur.com/'+match.group(2)
            print("replacing "+link+" with "+replacement)
            return replacement
        return link

    def unknown_command(self, bot, mess, cmd, args):
        self.random_chat(bot, mess, cmd, args)

    def random_chat(self, bot, mess, cmd, args):
        """Does things"""
        message = mess.getBody()
        # misc stuff here I guess
        reply = ""
        sender = self.get_sender_username(mess)

        titles = self.get_page_titles(message)
        if titles:
            reply = titles + "\n"

        if sender == self.nickname:
            return
        if ":lunaglee:" in message.lower():
            print self.get_sender_username(mess)
            self.bot.kick(chatroom, sender,
                      'Don\'t upset my big sister! :sweetiemad:')
            return
        if "c/d" in message.lower():
            reply = sender + ": " + random.choice(["c", "d"])
            return reply
        if "yiff" in message.lower() and utils.is_ping(self.nickname, message):
            reply = sender + ": yiff in hell, furfag :sweetiemad:"
            return reply
        if "chain" in message.lower():
            if sender == ":owl":
                self.deowl
            return
        if ":lunabeh:" in message.lower() and (sender == ":owl" or "luna" in sender.lower()):
            self.lunabeh_count = self.lunabeh_count + 1

        if self.lunabeh_count > self.lunabeh_top:
            self.lunabeh_top = randint(7, 15)
            self.lunabeh_count = 1
            reply = ":lunabeh:"
            return reply

        if len(reply.strip()):
            return reply.strip()

        # if message.lower().strip().endswith(":rdderp:"):
        #    return ":rdderp:"
        return self.log_mess(mess, bot)

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

    @botcmd
    def quiet(self, mess, args):
        '''I will only respond to pings'''
        self.chattiness = 0
        sender = self.get_sender_username(mess)
        if 'rainbow' in sender.lower():
            return ':rdderp: okay then'
        if 'luna' in sender.lower():
            return ':lunabeh: fine'
        if 'shard' in sender.lower():
            return "I'll be quiet if you make more emotes for me :sweetiedust:"
        if 'sparkle' in sender.lower():
            return "Yes, my princess :sweetiepleased:"
        if 'spike' in sender.lower():
            return "Oh my! A dragon! :sweetie: Of course I'll be quiet"
        return sender + ': Sorry! I\'ll be quiet'

    @botcmd(name='chat')
    def unquiet(self, mess, args):
        '''I will chat every once in a while'''
        self.chattiness = .025
        return self.get_sender_username(mess) + ': Ok, I\'ll start chatting again'

    @botcmd
    def quote(self, mess, args):
        '''Replays sass'''
        return self.sass.get_next()

    @botcmd
    def sass(self, mess, args):
        '''Remembers some sass to say back next time it is mentioned'''
        if len(args) > 400:
            return "Sass too long :sweetiedust"
        if not args.strip():
            return "What do you want me to remember?"
        if ":owl:" in args or self.get_sender_username(mess) == ':owl':
            return "No owls allowed! :sweetiedust:"
        reply = self.get_sender_username(mess) + ': I\'ll remember that!'
        self.sass.add_to_file(args)
        return reply

    #Karan = 30004306
    #Jita = 30000142
    #@botcmd
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
