import logging
import re
import random
from random import randint
from utils import logerrors, botcmd
from pprint import pprint

log = logging.getLogger(__name__)

class SweetieChat(object):
    urlregex = re.compile(r"((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@"+
                          ")?[A-Za-z0-9.-]+|(?:www.|[-;:&=\+\$,\w]+@)[A-Za"+
                          "-z0-9.-]+)((?:\/[\+~%\/.\w_-]*)?\??(?:[-\+=&:\/"+
                          ";%@.\w_]*)#?(?:[\w]*))?)")

    emotes = [':sweetie:', ':sweetiecrack:',
              ':sweetiederp:', ':sweetiedust:',
              ':sweetieglee:', ':sweetieidea:',
              ':sweetiemad:', ':sweetiepleased:',
              ':sweetieoops:', ':sweetieread:',
              ':sweetiescheme:', ':sweetieshake:',
              ':sweetieshrug:', ':sweetiesmug:',
              ':sweetiestare:', ':sweetietwitch:',
              ':egstare:', ':sweetiesiren:',
              ':sweetieskeptical:', ':sweetiedesk:',
              ':sweetiesalute:', ':sweetieawesome:',
              ':sweetiecreep:', ':sweetieeyes:',
              ':sweetiefsjal:', ':sweetielod:',
              ':sweetienom:', ':sweetieohyou:',
              ]

    lunabeh_top = 10
    lunabeh_count = 0
    target = '<target>'
    chattiness = .02
    cadance_musics_log = ResponsesFile('cadance_musics.log')

    def __init__(self, bot, actions, sass, chatroom, markov):
        self.bot = bot
        self.bot.load_commands_from(self)
        self.nickname = self.bot.nick
        self.actions = actions
        self.sass = sass
        self.chatroom = chatroom
        self.markov = markov

    def save_action(self, action_str):
        self.actions.add_to_file(action_str)

    def cuddle(self, message):
        log.debug('cuddle')
        if 'pets' in message.message_text:
            return '/me purrs ' + random.choice(self.emotes)
        action = self.actions.get_next()
        action = action.replace('<target>', message.sender_nick)
        return action + ' ' + random.choice(self.emotes)

    @logerrors
    def get_page_titles(self, message):
        matches = self.urlregex.findall(message)
        matches = [x[0] for x in matches]
        matches = list(map(self.imgur_filter, matches))
        matches = list(map(self.deviantart_filter, matches))
        results = list(map(self.get_page_title, matches))
        results = [result for result in results if result is not None]
        results = list(filter(self.title_filter, results))
        results = list(map(self.remove_extra_whitespace, results))
        if not len(results):
            return None
        return " / ".join(results)

    def get_page_title(self, url):
        if 'oembed' in url:
            return self.get_oembed_page_title(url)

        from bs4 import BeautifulSoup
        import requests
        try:
            headers = { 'user-agent': 'sweetiebot' }
            res = requests.get(url, timeout=5, headers=headers)
            if res.status_code != 200: return None
            # don't try and download big things
            content = res.raw.read(100000+1, decode_content=True)
            if len(content) > 100000:
                log.warning('skipping download of {} due to content-length > 100000')
                return
            if not 'html' in res.headers['content-type']:
                return
            soup = BeautifulSoup(res.text)
            return soup.title.string
        except Exception as e:
            log.warning("error fetching url "+url+" : "+str(e))

    def get_oembed_page_title(self, url):
        import json
        import requests
        try:
            headers = { 'user-agent': 'sweetiebot' }
            res = requests.get(url, timeout=5, headers=headers)
            result = json.loads(res.text)
            return result['title'] + ' by ' +result['author_name']
        except Exception as e:
            log.warning("error fetching url "+url+" : "+str(e))

    def title_filter(self, result):
        if (result.strip() == 'imgur: the simple image sharer'):
            return False
        if (result.strip() == 'Imgur'):
            return False
        if (result.strip() == 'Imgur: The most awesome images on the Internet'):
            return False
        if ('jiffier gifs through HTML5 Video Conversion' in result.strip()):
            return False
        return True

    def remove_extra_whitespace(self, result):
        result = result.replace('\n', '')
        result = result.replace('\r', '')
        result = re.sub('\s+', ' ', result)
        return result

    def imgur_filter(self, link):
        imgurregex = re.compile(r'^http(s)?://i.imgur.com/([a-zA-Z0-9]*)\..*$')
        match = imgurregex.match(link)
        if (match):
            replacement = 'http://imgur.com/'+match.group(2)
            log.debug("replacing "+link+" with "+replacement)
            return replacement
        return link

    def deviantart_filter(self, link):
        devartregex = re.compile(r'^http(s)?://\w+\.deviantart\.[\w/]+-(\w+)\.\w+$')
        match = devartregex.match(link)
        if (match):
            replacement = 'http://backend.deviantart.com/oembed?url=http://fav.me/'+match.group(2)
            log.debug("replacing "+link+" with "+replacement)
            return replacement
        return link
    def has_youtube_link(self,link):
        youtuberegex = re.complile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
        match = youtuberegex.match(link)
        log.debug("Matched youtube link")
        if (match):
            return True
        return False
    def do_cadance_musics(self, mess):
        if (mess.sender_jid == "princess_cadence@friendshipismagicsquad.com"):
            titles = self.get_page_titles(mess.message_text)
            has_youtube = False            
            for title in titles:
                if (self.has_youtube_link(title)):
                    has_youtube = True
                    break
            if (has_youtube):
                cadance_musics_log.add_to_file(mess.message_text)
                log.debug("Added music to log")

    @logerrors
    def random_chat(self, mess):
        """Does things"""
        message = mess.message_text
        sender = mess.sender_nick
        self.markov.store_message(message)

        #logs Cadance musics
        self.do_cadance_musics(mess)

        titles = self.get_page_titles(message)
        if titles:
            return titles

        #if ":lunaglee:" in message.lower():
        #    self.bot.kick(sender, 'Don\'t upset my big sister! :sweetiemad:')
        #    return

        if "c/d" in message.lower():
            return sender + ": " + random.choice(["c", "d"])

        is_ping = mess.is_ping
        if "yiff" in message.lower() and is_ping:
            return sender + ": yiff in hell, furfag :sweetiemad:"

        if ":lunabeh:" in message.lower() and (sender == ":owl" or "luna" in sender.lower()):
            self.lunabeh_count = self.lunabeh_count + 1

        if self.lunabeh_count > self.lunabeh_top:
            self.lunabeh_top = randint(7, 15)
            self.lunabeh_count = 1
            return ":lunabeh:"

        if message.startswith('/me ') and is_ping:
            return self.cuddle(mess)

        if False: #is_ping or random.random() < self.chattiness:
            markov_response = self.markov.get_message(message)
            if markov_response:
                return markov_response

        if is_ping:
            return self.sass.get_next()

    @botcmd
    def cadance(self, message):
        return self.cadance_musics_log.get_next()

    @botcmd(hidden=True)
    def quiet(self, message):
        '''I will only respond to pings'''
        self.chattiness = 0
        sender = message.sender_nick
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

    @botcmd(name='chat', hidden=True)
    def unquiet(self, message):
        '''I will chat every once in a while'''
        self.chattiness = .025
        return message.sender_nick + ': Ok, I\'ll start chatting again'

    @botcmd
    def sass(self, message):
        '''[message] Remembers some sass to say back next time it is mentioned'''
        if len(message.args) > 400:
            return "Sass too long :sweetiedust"
        if not message.args.strip():
            return "What do you want me to remember?"
        if ":owl:" in message.args or message.sender_nick == ':owl':
            return "No owls allowed! :sweetiedust:"
        reply = message.sender_nick + ': I\'ll remember that!'
        self.sass.add_to_file(message.args)
        return reply

    @botcmd
    def choose(self, message):
        '''[choices] Choose one of a (comma-separated) list of options'''
        return random.choice(list(map(lambda e: e.strip(), message.args.split(","))))
