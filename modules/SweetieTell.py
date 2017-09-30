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
        self.nicktojid = NickToJidTracker(self.bot, self.store)

    def enc(self, str):
        return str.encode('utf-8')

    def dec(self, bytes):
        return bytes.decode('utf-8')

    @botcmd
    def tell(self, message):
        '''[user] [message] Notify a user the next time they speak in chat'''
        if message.is_pm: return 'Sorry, you can\'t use !tell in a PM'
        if not message.nick_reason: return "A target user and message are required"
        sender_nick = message.sender_nick
        sendee_nick, mess = message.nick_reason
        if not mess: return "A message is required"
        sendee_jid = self.bot.get_jid_from_nick(sendee_nick)
        sendee_jid = sendee_jid or self.nicktojid.get_jid_from_nick(sendee_nick)
        sender_jid = message.user_jid
        log.debug('sender_nick {} sendee_nick {} mess {} sendee_jid {} sender_jid {}'.format(
            sender_nick, sendee_nick, mess, sendee_jid, sender_jid))

        if sendee_nick == message.nickname:
            return 'I\'m right here, you know'
        if sendee_jid is None:
            return 'Sorry, I don\'t know who \'{}\' is'.format(sendee_nick)
        if sender_jid is None:
            return 'I can\'t figure out who you are: is this channel hiding JIDs?'
        if sender_jid == sendee_jid:
            return 'Talking to yourself is more efficient in real life than on jabber'

        existing_messages = self.get(sendee_jid)
        existing_message = existing_messages.get(self.enc(str(sender_jid)), None)
        if existing_message is not None:
            self.set(sendee_jid, sender_jid, self.dec(existing_message) + '\n' + mess)
            return 'Message received for {} (appended to previous message)'.format(sendee_jid)
        if sendee_nick and mess:
            self.set(sendee_jid, sender_jid, '{} left you a message: {}'.format(sender_nick, mess))
            return 'Message received for {}'.format(sendee_jid)

    def _key(self, jid):
        return 'tell:{}'.format(str(jid))

    def get_messages_for(self, message):
        key = self._key(message.user_jid)
        messages = self.store.hvals(key)
        messages = list(map(lambda x: x.decode('utf-8'), messages))
        if len(messages):
            self.store.delete(key)
            return message.sender_nick + ", " + "\n".join(messages)

    def set(self, jid, senderjid, message):
        self.store.hset(self._key(jid), str(senderjid), message)

    def get(self, jid):
        return self.store.hgetall(self._key(jid))

class NickToJidTracker(object):
    def __init__(self, bot, store):
        self.store = store
        self.bot = bot
        self.bot.add_presence_handler(self.on_presence)

    def on_presence(self, presence):
        nick = presence.muc_jid.resource
        jid = presence.user_jid.bare
        log.debug('setting jid for nick {} to {}'.format(nick, jid))
        self.set_jid_for_nick(nick, jid)

    def get_jid_from_nick(self, nick):
        result = self.store.get(self._key(nick))
        if result: return result.decode('utf-8')

    def set_jid_for_nick(self, nick, jid):
        self.store.set(self._key(nick), jid)

    def _key(self, nick):
        return 'jidfornick:{}'.format(nick)

