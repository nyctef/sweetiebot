import logging
import re
import xmpp
import utils
import random
from utils import logerrors, randomstr
from jabberbot import botcmd
from SweetieRedis import SweetieRedis


class SweetieChat():

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

    id_dic = {"": ""}
    id_list = {}
    chain_length = 2
    min_reply_length = 3
    chattiness = .02
    max_words = 30
    messages_to_generate = 100
    lunabeh_top = 10
    lunabeh_count = 0
    target = '<target>'

    def __init__(self, bot, redis, actions, sass):
        self.bot = bot
        self.bot.load_commands_from(self)
        self.redis = redis
        self.nickname = self.bot.nickname
        self.actions = actions
        self.sass = sass

    def get_sender_username(self, mess):
        return self.bot.get_sender_username(mess)

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
            words.append(self.redis.stop_word)

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
            words = key.split(self.redis.separator)

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
