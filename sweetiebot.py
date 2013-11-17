#!/usr/bin/env python
# coding: utf-8


from jabberbot import JabberBot, botcmd
from datetime import datetime
import re
import time
import urllib
import xmpp
from xml.etree import ElementTree as ET
import random
from random import randint
import difflib
import redis
import unicodedata
import sys
import logging
from functools import wraps


def logerrors(func):
    @wraps(func)
    def logged(self, *args, **kwargs):
        try: return func(self, *args, **kwargs)
        except Exception as e: 
            print 'Error! '+e
            logging.error(str(e))
            return "My code is problematic :sweetieoops"
    return logged

class MUCJabberBot(JabberBot):

    ''' Add features in JabberBot to allow it to handle specific
    caractheristics of multiple users chatroom (MUC). '''

    flood_protection = 0
    flood_delay = 5
    PING_FREQUENCY = 10
    def __init__(self, *args, **kwargs):
        ''' Initialize variables. '''

        # answer only direct messages or not?
        self.only_direct = kwargs.get('only_direct', False)
        
        try:
            del kwargs['only_direct']
        except KeyError:
            pass

        # initialize jabberbot
        super(MUCJabberBot, self).__init__(*args, **kwargs)

        # create a regex to check if a message is a direct message
        user, domain = str(self.jid).split('@')
        self.direct_message_re = re.compile('^%s(@%s)?[^\w]? ' \
                % (user, domain))

    def callback_message(self, conn, mess):
        ''' Changes the behaviour of the JabberBot in order to allow
        it to answer direct messages. This is used often when it is
        connected in MUCs (multiple users chatroom). '''
        
        message = mess.getBody()
        if self.direct_message_re.match(message):
            mess.setBody(' '.join(message.split(' ', 1)[1:]))
            return super(MUCJabberBot, self).callback_message(conn, mess)
        elif not self.only_direct:
            return super(MUCJabberBot, self).callback_message(conn, mess)


class Sweetiebot(MUCJabberBot):
    kick_owl_delay = 7200
    last_owl_kick = 0
    id_dic = {"":""}
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
    mods = ['Blighty','Nyctef','Princess Luna','Princess Cadence','Rainbow Dash','Twilight Sparkle','Big Macintosh','Fluttershard','Rainbow Dash']
    emotes = [':sweetie:',':sweetiecrack:',\
              ':sweetiederp:',':sweetiedust:',\
              ':sweetieglee:',':sweetieidea:',\
              ':sweetiemad:',':sweetiepleased:',\
              ':sweetieoops:',':sweetieread:',\
              ':sweetiescheme:',':sweetieshake:',\
              ':sweetieshrug:',':sweetiesmug:',\
              ':sweetiestare:',':sweetietwitch:',\
              ':egstare:',':sweetiesiren:']
    preferred_endings = ['.','~','!']
    banned_endings = ['and','or','aboard','about','above','across','after','against','along','amid','among',\
                    'anti','around','as','at','before','behind','below','beneath','beside','besides',\
                    'between','beyond','but','by','concerning','considering','despite','down','during',\
                    'except','excepting','excluding','following','for','from','in','inside','into','like',\
                    'minus','near','of','off','on','onto','opposite','outside','over','past','per','plus',\
                    'regarding','round','save','since','than','through','to','toward','towards','under',\
                    'underneath','unlike','until','up','upon','versus','via','with','within','without']

    def __init__(self, nickname='Sweetiebutt', *args, **kwargs):
        self.nickname = nickname
        resource = 'sweetiebutt' + ('%08x' % random.randrange(16**8))
        super(Sweetiebot, self).__init__(*args, res=resource, **kwargs)
        self.redis_conn = redis.Redis('localhost')

    def remove_dup(self, outfile, infile):
        lines_seen = set() # holds lines already seen
        in_f = open(infile, "r")
        for line in in_f:
            if line not in lines_seen and not ":lunaglee:" in line: # not a duplicate
                if not any(i in line for i in ('#','/','\\')):
                    lines_seen.add(line)		
        in_f.close()
        out_f = open(outfile, "w")
        out_f.writelines(sorted(lines_seen))
        out_f.close()
        return

    def make_key(self, k):
        return '-'.join((self.prefix, k))
    
    def sanitize_message(self, message):
        if "http" in message:
            return ""
        if "####" in message:
            return ""
        
        return re.sub('[\"\']', '', message.lower())

    def roll_prim(self,dice = 1, sides = 6):
        try: return [randint(1,sides) for i in range(dice)]
        except: return []
        
    def save_action(self, action_str):
        s = action_str.lower()
        s = s.replace(self.nickname.lower(), self.target)
        f = open('Sweetiebot.actions','a')
        f.write(s)
        f.close()
        self.remove_dup('Sweetiebot.actions','Sweetiebot.actions')

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
            next_word = self.redis_conn.srandmember(self.make_key(key))
            if not next_word:
                break
            
            # create a new key combining the end of the old one and the next_word
            key = self.separator.join(words[1:] + [next_word])
        return ' '.join(gen_words)

    def fix_ping(self, message):
        message = message.replace(self.nickname+": ","")
        message = message.replace(self.nickname.lower()+": ","")
        return message

    def is_ping(self, message):
        if self.nickname.lower() in message.lower():
            return True
        else:
            return False

    def cuddle(self, mess):
        message = mess.getBody().lower()
        if 'pets' in message:
            return '/me purrs '+ random.choice(self.emotes)
        #self.save_action(message.replace('\n',' ')+ '\n')
        f = open('Sweetiebot.actions','r')
        reply = self.random_line(f)
        reply = reply.replace(self.target,self.get_sender_username(mess).encode('utf-8')) 
        return reply + ' ' + random.choice(self.emotes)

    def log_mess(self, mess):
        # speak only when spoken to, or when the spirit moves me
        jid = mess.getFrom()
        props = mess.getProperties()
        message = mess.getBody()
        message_true = mess.getBody()
        message_weight = 0
        say_something = False
        if xmpp.NS_DELAY in props:
            return
        if not message:
            return
        if self.get_sender_username(mess)==self.nickname:
            return
        if self.jid.bareMatch(jid):
            return
        if self.is_ping(message):
            say_something = True
        if not say_something:
            say_something = random.random() < self.chattiness
                
        messages = []
        # use a convenience method to strip out the "ping" portion of a message
        if self.is_ping(message):
            message = self.fix_ping(message)

        if message_true.startswith('/'):
            if message_true.startswith('/me ') and self.is_ping(message_true):
                return self.cuddle(mess)
            return

        if say_something:
            print '# ' + self.get_sender_username(mess).encode('utf-8') + ':' + message_true.encode('utf-8')
        else:
            print '  ' + self.get_sender_username(mess).encode('utf-8') + ':' + message_true.encode('utf-8')


        # split up the incoming message into chunks that are 1 word longer than
        # the size of the chain, e.g. ['what', 'up', 'bro'], ['up', 'bro', '\x02']
        for words in self.split_message(self.sanitize_message(message)):
            # grab everything but the last word
            key = self.separator.join(words[:-1])
            # add the last word to the set
            self.redis_conn.sadd(self.make_key(key), words[-1])
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
        elif self.is_ping(message_true): #If was pinged but couldn't think of something relevant, reply with something generic.
            print 'Quoting instead...'
            return self.quote(mess,'')

    def callback_message(self, conn, mess):
        ''' Changes the behaviour of the JabberBot in order to allow
        it to answer direct messages. This is used often when it is
        connected in MUCs (multiple users chatroom). '''
        #fuck you unicode
        message = mess.getBody()
        props = mess.getProperties()
        jid = mess.getFrom()
        try:
            if self.direct_message_re.match(message):
                mess.setBody(' '.join(message.split(' ', 1)[1:]))
                super(Sweetiebot, self).callback_message(conn, mess)
        except TypeError:
            return
        if not message:
            return
        if xmpp.NS_DELAY in props:
            return
        if self.jid.bareMatch(jid):
            return
        if self.is_ping(message):
            np_message = self.fix_ping(message)
        else:
            np_message = message
        if ' ' in np_message:
            command, args = np_message.split(' ',1)
        else:
            command, args = np_message, ''

        cmd = command.lower()
        if cmd in self.commands:
            if self.is_ping(message):
                mess.setBody(np_message)
                super(Sweetiebot, self).callback_message(conn, mess)
            else:
                return
        else:
            reply = self.unknown_command(mess, cmd, args)
            if reply is None:
                return
            if reply:
                self.send_simple_reply(mess, reply)
        return

    def random_line(self,afile):
        try:
            line = next(afile)
        except Exception as e:
            print repr(e) + " " + str(e)
            return "/me slaps <target> with a large trout."
        for num, aline in enumerate(afile):
            if random.randrange(num + 2): continue
            line = aline

        line = line.replace('\n','')
        return line

    def on_ping_timeout(self):
        logging.info('Terminating due to PING timeout.')
        self.quit(1)

    def unknown_command(self, mess, cmd, args):
        """Does things"""
        message = mess.getBody()
        #misc stuff here I guess
        reply = ""
        if self.get_sender_username(mess) == self.nickname:
            return
        if ":lunaglee:" in message.lower():
            print self.get_sender_username(mess)
            self.kick(chatroom,self.get_sender_username(mess),'Don\'t upset my big sister! :sweetiemad:')
            return
        if "c/d" in message.lower():
            reply = self.get_sender_username(mess) + ": " + random.choice(["c","d"])
            return reply
        if "yiff" in message.lower() and self.is_ping(message):
            reply = self.get_sender_username(mess) + ": yiff in hell, furfag :sweetiemad:"
            return reply
        if "chain" in message.lower():
            if self.get_sender_username(mess) == ":owl":
                self.deowl;
            return
        if ":lunabeh:" in message.lower() and self.get_sender_username(mess) == ":owl":
            self.lunabeh_count = self.lunabeh_count + 1
            if self.lunabeh_count > self.lunabeh_top:
                self.lunabeh_top = randint(2,10)
                self.lunabeh_count = 1
                reply = ":lunabeh:"
                return reply
        return self.log_mess(mess)
    
    def get_prices(self, id, system):
        url = "http://api.eve-central.com/api/marketstat?usesystem=" + \
              str(system) + \
              "&typeid=" + \
              str(id)
        root = ET.parse(urllib.urlopen(url)).getroot()
        
        buy = root[0][0][0][2].text # top buy
        sell = root[0][0][1][3].text # low sell
        buy = '{0:,}'.format(float(buy))
        sell = '{0:,}'.format(float(sell))
        r = 'buy: ' + buy + ' isk, sell: ' + sell + ' isk'
        return r

    def id_lookup(self,name):
        test = name
        test = test.upper()
        reply = None
        i_id = None
        i_name = None
        if len(self.id_dic) <= 1:
            f = open('typeid.txt')
            line = f.readline()
            line = line.replace("\n","")
            while(len(line) > 0):
                key, item_name = line.split('=',1)
                self.id_dic[item_name] = int(key)
                line = f.readline().replace("\n","")
            f.close()

        if test in list(self.id_dic.keys()):
            reply = self.id_dic[test]
        else:
            maybe = difflib.get_close_matches(test,list(self.id_dic.keys()),1)
            if len(maybe) > 0:
                print ("maybe meant "+ maybe[0])
                if maybe[0] in list(self.id_dic.keys()):
                    i_id = self.id_dic[maybe[0]]
                    i_name = maybe[0]
        return i_id, i_name

    def deowl(self, mess, args):
        '''Only kicks :owl, long cooldown'''
        self.kick('general@talk.friendshipismagicsquad.com',':owl', reason=':sweetiestare:')
        return

    @botcmd
    @logerrors
    def hype(self, mess, args):
        """Get hype! Print time until S4 starts"""
        #print 'getting hype ..'
        hypetime = datetime.strptime('03:00PM 2013-11-23', '%I:%M%p %Y-%m-%d')
        now = datetime.now()
        diff = hypetime - now
        message = 'GET HYPE! ONLY {0} DAYS, {1} HOURS, {2} MINUTES AND {3} SECONDS UNTIL SEASON FOUR!'\
                .format(diff.days, diff.seconds // 3600, (diff.seconds//60)%60, diff.seconds%60)
        #print message
        return message

    @botcmd
    def bye(self, mess, args):
        '''Makes me restart! Blighties only!'''
        if self.get_sender_username(mess) == 'Blighty':
            self.quit()

#    @botcmd
    def yell(self, mess, args):
        '''Yells at everyone Blighties only!'''
        if self.get_sender_username(mess) == 'Blighty':
            self.broadcast(args, True)
          
    @botcmd
    def quiet(self, mess,args):
        '''I will only respond to pings'''
        self.chattiness = -1
        return self.get_sender_username(mess) + ': Sorry! I\'ll be quiet'

    @botcmd
    def chat(self, mess, args):
        '''I will chat every once in a while'''
        self.chattiness = .025
        return self.get_sender_username(mess) + ': Ok, I\'ll start chatting again'

    @botcmd
    def quote(self, mess, args):
        '''Replays sass'''
        f=open('Sweetiebot.sass','r')
        return self.random_line(f)

    @botcmd
    def sass(self, mess, args):
        '''Remembers some sass to say back next time it is mentioned'''
        if len(args) > 400:
            return
        if args.isspace():
            return
        f = open('Sweetiebot.sass','a')

        clean_args = args.replace('\n',' ')
        f.write(clean_args + '\n')
        f.close()
        reply = self.get_sender_username(mess) + ': I\'ll remember that!'
        self.remove_dup('Sweetiebot.sass','Sweetiebot.sass')
        return reply

    #Karan = 30004306
    #Jita = 30000142
#    @botcmd
    def karan(self, mess, args):
        '''Looks up Karan Prices, use !karan [ITEM NAME]'''
        id,name = self.id_lookup(args)
        if id is None:
            return ''
        reply = self.get_prices(id,30004306)
        reply = reply = self.get_sender_username(mess) + ': '+name.title() + ' - ' + reply
        return reply

    @botcmd
    def jita(self, mess, args):
        '''Looks up Jita Prices, use !jita [ITEM NAME]'''
        id,name = self.id_lookup(args)
        if id is None:
            return ''
        reply = self.get_prices(id,30000142)
        reply = reply = self.get_sender_username(mess) + ': '+name.title() + ' - ' + reply
        return reply

    @botcmd
    def remove (self, mess, args):
        '''kicks! I'm a little drunk right now...hope this works'''
        if self.get_sender_username(mess) in self.mods:
            self.kick(chatroom,xmpp.JID(args),'out! :sweetiemad:')
        return
        
    @botcmd
    def roll(self, mess, args):
        '''Accepts rolls in the form of 'roll 1d6' and similar -- max 25 dice'''
        brup = args.split(' ')
        reply = ''
        for args in brup: 
            try:
              dice, sides = map(int,args.split('d',1))
            except:
              return
            if dice > 25:
                return "Too many variables in possibilty space, abort!"
            if sides > 20000000:
                return "Sides of dice too small, can't see what face is upright!"
            if sides < 2:
                return "How do you make a dice with less than two sides?"
            if dice < 1:
                return "You want me to roll...less than one dice?"
            rolls = self.roll_prim(dice, sides)
            if len(rolls) < 1:
              return
            new_dice = ', '.join(map(str,rolls))
            if not reply:
                reply = new_dice
            else:
                reply = reply + " ~ " + new_dice
        return reply

#    @botcmd
    def ban(self, mess, args):
        """Kicks user from muc
        Works only with sufficient rights."""
        NS_MUCADMIN = 'http://jabber.org/protocol/muc#admin'
        item = xmpp.simplexml.Node('item')
        item.setAttr('nick', nick)
        item.setAttr('affiliation','outcast')
        item.setAttr('role', 'none')
        iq = xmpp.Iq(typ='set', queryNS=NS_MUCADMIN, xmlns=None, to=room,
                payload=set([item]))
        if reason is not None:
            item.setTagData('reason', reason)
        self.connect().send(iq)

    @botcmd
    def date(self, mess, args):
        '''Returns the current date'''
        reply = datetime.now().strftime('%Y-%m-%d')
        reply = self.get_sender_username(mess) + ': ' + reply
        self.send_simple_reply(mess, reply)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename='sweetiebot.log',level=logging.INFO)

    #username = 'blighted@friendshipismagicsquad.com/sweetiebutt'
    #username = 'sweetiebot@friendshipismagicsquad.com/sweetiebutt'
    username = 'nyctef@friendshipismagicsquad.com'
    password = 'stopbeingbadluna' #password here
    chatroom = 'general@conference.friendshipismagicsquad.com'
    nickname = 'Sweetiebutt'
    debug = False

    import sys
    if '--test' in sys.argv:
        chatroom = 'sweetiebot_playhouse@conference.friendshipismagicsquad.com'
        debug = True

    sweet = Sweetiebot(nickname, username, password, only_direct=False, command_prefix='')
    print sweet.nickname + ' established!'
    print username
    print 'Joining Room:' + chatroom
    sweet.join_room(chatroom, sweet.nickname)
    print 'Joined!'
    sweet.serve_forever()


