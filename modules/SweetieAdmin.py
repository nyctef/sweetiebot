import logging
import xmpp
from utils import logerrors, randomstr
from jabberbot import botcmd
import re
from datetime import datetime

class SweetieAdmin():
    mods = [
        "luna@friendshipismagicsquad.com",
        "gielnor@friendshipismagicsquad.com",
        "xyyxshard@friendshipismagicsquad.com",
        "sykedoc@friendshipismagicsquad.com",
        "twilight_sparkle@friendshipismagicsquad.com",
        "princess_cadence@friendshipismagicsquad.com",
        "seven@friendshipismagicsquad.com",
        "nyctef@friendshipismagicsquad.com",
    ]

    _kick = "kick"
    _ban = "ban"
    _unban = "unban"

    def __init__(self, bot, chatroom):
        self.bot = bot
        self.bot.load_commands_from(self)
        self.chatroom = chatroom

    def get_sender_username(self, message):
        return self.bot.get_sender_username(message)

    def nick_is_mod(self, nick):
        return self.bot.get_jid_from_nick(nick) in self.mods

    @staticmethod
    def iq_for_kickban(room, nick, jid, reason, kickban_type):
        NS_MUCADMIN = 'http://jabber.org/protocol/muc#admin'
        item = xmpp.simplexml.Node('item')
        if nick is not None:
            item.setAttr('nick', nick)
        if jid is not None:
            item.setAttr('jid', jid)

        if kickban_type is SweetieAdmin._kick:
            item.setAttr('role', 'none')
        if kickban_type is SweetieAdmin._ban:
            item.setAttr('affiliation', 'outcast')
        if kickban_type is SweetieAdmin._unban:
            item.setAttr('affiliation', 'none')

        iq = xmpp.Iq(typ='set', queryNS=NS_MUCADMIN, xmlns=None, to=room,
                     payload=set([item]))
        if reason is not None:
            item.setTagData('reason', reason)
        return iq

    def _kickban(self, room, nick=None, jid=None, reason=None,
                 kickban_type=None):
        """Kicks user from muc
        Works only with sufficient rights."""
        logging.debug('rm:{} nk{} jid{} rsn{} isBan{}'.format(
            room, nick, jid, reason, kickban_type))

        iq = SweetieAdmin.iq_for_kickban(room, nick, jid, reason, kickban_type)

        self.bot.send_iq(iq, self._kickban_response_handler())

    def _kickban_response_handler(self):
        def handler(session, response):
            if response is None:
                self.chat("Did that work? I timed out for a moment there")
                return
            error = response.getTag('error')
            if error is not None:
                not_allowed = error.getTag('not-allowed')
                if not_allowed is not None:
                    self.chat('Sweetiebot used Kick! It\'s not very effective...')
                    return
                text = error.getTag('text')
                if text is None:
                    self.chat('Something\'s fucky...')
                    return
                self.chat(str(text))
        return handler

    def get_nick_reason(self, args):
        nick = None
        reason = None
        match = re.match("\s*'([^']*)'(.*)", args) or\
            re.match("\s*\"([^\"]*)\"(.*)", args) or\
            re.match("\s*(\S*)(.*)", args)
        if match:
            nick = match.group(1)
            reason = match.group(2).strip()
        return nick, reason

    def chat(self, message):
        self.bot.send(self.chatroom, message, message_type='groupchat')

    @botcmd
    def banlist(self, mess, args):
        return self.listbans(mess, args)

    @botcmd
    @logerrors
    def listbans(self, mess, args):
        """List the current bans. Requires admin"""
        id = 'banlist'+randomstr()
        NS_MUCADMIN = 'http://jabber.org/protocol/muc#admin'
        item = xmpp.simplexml.Node('item')
        item.setAttr('affiliation', 'outcast')
        iq = xmpp.Iq(
            typ='get', attrs={"id": id}, queryNS=NS_MUCADMIN, xmlns=None, to=self.chatroom,
            payload=set([item]))

        def handleBanlist(session, response):
            if response is None:
                return "timed out waiting for banlist"
            res = ""
            items = response.getChildren()[0].getChildren()
            for item in items:
                if item.getAttr('jid') is not None:
                    res += "\n" + item.getAttr('jid') + ": "+str(item.getChildren()[0].getData())
            self.chat(res)

        self.bot.send_iq(iq, handleBanlist)

    @botcmd(name='ban')
    @logerrors
    def ban(self, mess, args):
        '''bans user. Requires admin and a reason

        nick can be wrapped in single or double quotes'''

        nick, reason = self.get_nick_reason(args)

        sender = self.get_sender_username(mess)
        if not self.nick_is_mod(sender):
            return "nooope"
        if not len(reason):
            return "A reason must be provided"

        print("trying to ban "+nick+" with reason "+reason)
        self._kickban(self.chatroom, nick, None, 'Banned by '+sender +
                    ': ['+reason+'] at '+datetime.now().strftime("%I:%M%p on %B %d, %Y"),
                      kickban_type=self._ban)

    @botcmd(name='unban')
    @logerrors
    def un(self, mess, args):
        '''unbans a user. Requires admin and a jid (check listbans)

        nick can be wrapped in single or double quotes'''

        jid = args

        sender = self.get_sender_username(mess)
        if self.nick_is_mod(sender):
            print("trying to unban "+jid)
            self._kickban(self.chatroom, jid=jid, kickban_type=self._unban)
        else:
            return "noooooooope."

    @botcmd(name='kick')
    @logerrors
    def remove(self, mess, args):
        '''kicks user. Requires admin and a reason

        nick can be wrapped in single or double quotes'''

        nick, reason = self.get_nick_reason(args)

        sender = self.get_sender_username(mess)
        if not self.nick_is_mod(sender):
            return "noooooooope."

        print("trying to kick "+nick+" with reason "+reason)
        self._kickban(self.chatroom, nick=nick, reason=reason,
                      kickban_type=self._kick)

    def kick(self, nick, reason):
        self._kickban(self.chatroom, nick=nick, reason=reason,
                      kickban_type=self._kick)

    #@botcmd()
    #@logerrors
    #def debug(self, mess, args):
    #    # what could possibly go wrong
    #    return str(eval(args))
