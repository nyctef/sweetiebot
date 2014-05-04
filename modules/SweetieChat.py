import logging
import re
import utils
import random
from random import randint
from jabberbot import botcmd
from utils import logerrors

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

    def __init__(self, bot, actions, sass, chatroom, markov):
        self.bot = bot
        self.bot.load_commands_from(self)
        self.nickname = self.bot.nickname
        self.actions = actions
        self.sass = sass
        self.chatroom = chatroom
        self.markov = markov

    def get_sender_username(self, mess):
        return self.bot.get_sender_username(mess)

    def save_action(self, action_str):
        self.actions.add_to_file(action_str)

    def cuddle(self, mess):
        logging.debug('cuddle')
        message = mess.getBody().lower()
        if 'pets' in message:
            return '/me purrs ' + random.choice(self.emotes)
        action = self.actions.get_next()
        action = action.replace('<target>', self.get_sender_username(mess))
        return action + ' ' + random.choice(self.emotes)

    @logerrors
    def get_page_titles(self, message):
        matches = self.urlregex.findall(message)
        matches = map(lambda x: x[0], matches)
        matches = map(self.imgur_filter, matches)
        matches = map(self.deviantart_filter, matches)
        results = map(self.get_page_title, matches)
        results = [result for result in results if result is not None]
        results = filter(self.title_filter, results)
        results = map(self.remove_extra_whitespace, results)
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
            if not 'html' in res.headers['content-type']:
                return
            soup = BeautifulSoup(res.text)
            return soup.title.string
        except Exception as e:
            print "error fetching url "+url+" : "+str(e)

    def get_oembed_page_title(self, url):
        import json
        import requests
        try:
            headers = { 'user-agent': 'sweetiebot' }
            res = requests.get(url, timeout=5, headers=headers)
            result = json.loads(res.text)
            print(result)
            return result['title'] + ' by ' +result['author_name']
        except Exception as e:
            print "error fetching url "+url+" : "+str(e)

    def title_filter(self, result):
        if (result.strip() == 'imgur: the simple image sharer'):
            return False
        if (result.strip() == 'Error - Test Forums Please Ignore'):
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
            print("replacing "+link+" with "+replacement)
            return replacement
        return link

    def deviantart_filter(self, link):
        devartregex = re.compile(r'^http(s)?://\w+\.deviantart\.[\w/]+-(\w+)\.\w+$')
        match = devartregex.match(link)
        if (match):
            replacement = 'http://backend.deviantart.com/oembed?url=http://www.deviantart.com/gallery/%23/'+match.group(2)
            print("replacing "+link+" with "+replacement)
            return replacement
        return link

    def random_chat(self, bot, mess, cmd, args):
        """Does things"""
        message = mess.getBody()
        sender = self.get_sender_username(mess)
        self.markov.store_message(message)

        titles = self.get_page_titles(message)
        if titles:
            return titles

        if sender == self.nickname:
            return

        if ":lunaglee:" in message.lower():
            print self.get_sender_username(mess)
            self.bot.kick(self.chatroom, sender,
                          'Don\'t upset my big sister! :sweetiemad:')
            return

        if "c/d" in message.lower():
            return sender + ": " + random.choice(["c", "d"])

        if "yiff" in message.lower() and utils.is_ping(self.nickname, message):
            return sender + ": yiff in hell, furfag :sweetiemad:"

        if ":lunabeh:" in message.lower() and (sender == ":owl" or "luna" in sender.lower()):
            self.lunabeh_count = self.lunabeh_count + 1

        if self.lunabeh_count > self.lunabeh_top:
            self.lunabeh_top = randint(7, 15)
            self.lunabeh_count = 1
            return ":lunabeh:"

        is_ping = utils.is_ping(self.nickname, message)
        if message.startswith('/me ') and is_ping:
            return self.cuddle(mess)

        markov_response = self.markov.log_mess(message)
        if markov_response:
            return markov_response

        if is_ping:
            return self.quote(mess, None)

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

