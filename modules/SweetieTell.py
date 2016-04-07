from utils import botcmd, logerrors
from sleekxmpp import JID
from datetime import datetime
import logging
import re
from pprint import pprint

log = logging.getLogger(__name__)

class SweetieTell(object):
    def __init__(self, bot, store):
        self.store = store
        self.bot = bot
        self.bot.load_commands_from(self)

    def get_nick_message(self, args):
        nick = None
        message = None
        match = re.match("\s*'([^']*)'(.*)", args) or\
            re.match("\s*\"([^\"]*)\"(.*)", args) or\
            re.match("\s*(\S*)(.*)", args)
        if match:
            nick = match.group(1)
            message = match.group(2).strip()
        return nick, message

    def dec(self, bytes):
        return bytes.decode('utf-8')

    @botcmd
    def tell(self, message):
        '''[user] [message] Notify a user the next time they speak in chat'''
        if message.is_pm: return 'Sorry, you can\'t use !tell in a PM'
        sender_nick = message.sender_nick
        sendee_nick, mess = self.get_nick_message(message.args)
        sendee_jid = self.bot.get_jid_from_nick(sendee_nick)
        sender_jid = message.user_jid
        existing_messages = self.get(sendee_jid)
        log.debug('sender_nick {} sendee_nick {} mess {} sendee_jid {} sender_jid {}'.format(
            sender_nick, sendee_nick, mess, sendee_jid, sender_jid))
        #pprint(existing_messages)
        if sendee_nick == message.nickname:
            return 'I\'m right here, you know'
        if sendee_jid is None:
            return 'Sorry, I don\'t know who \'{}\' is'.format(sendee_nick)
        if sender_jid is None:
            return 'I can\'t figure out who you are: is this channel hiding JIDs?'
        if str(sender_jid) in map(self.dec, existing_messages.keys()):
            return 'Sorry, you\'ve already left a message for {}'.format(sendee_nick)
        if sender_jid == sendee_jid:
            return 'Talking to yourself is more efficient in real life than on jabber'
        if sendee_nick and mess:
            self.set(sendee_jid, sender_jid, '{} left you a message: {}'.format(sender_nick, mess))
            return 'Message received for {}'.format(sendee_nick)

    def _key(self, jid):
        return 'tell:{}'.format(str(jid))

    def get_messages_for(self, message):
        key = self._key(message.user_jid)
        messages = self.store.hvals(key)
        messages = list(map(lambda x: x.decode('utf-8'), messages))
        if len(messages):
            self.store.delete(key)
            return "\n".join(messages)

    def set(self, jid, senderjid, message):
        self.store.hset(self._key(jid), str(senderjid), message)

    def get(self, jid):
        return self.store.hgetall(self._key(jid))

