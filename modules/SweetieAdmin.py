import logging
import xmpp
from utils import logerrors, randomstr
from jabberbot import botcmd
import re
from datetime import datetime

log = logging.getLogger(__name__)

class SweetieAdmin(object):
    _kick = "kick"
    _ban = "ban"
    _unban = "unban"

    def __init__(self, bot, chatroom, mods):
        self.bot = bot
        self.bot.load_commands_from(self)
        self.chatroom = chatroom
        self.mods = mods

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
                 kickban_type=None, on_success=None, on_failure=None):
        """Kicks user from muc
        Works only with sufficient rights."""
        log.debug('rm:{} nk{} jid{} rsn{} isBan{}'.format(
            room, nick, jid, reason, kickban_type))

        iq = SweetieAdmin.iq_for_kickban(room, nick, jid, reason, kickban_type)

        self.bot.send_iq(iq, self._kickban_response_handler(on_success,
                                                            on_failure))

    def _kickban_response_handler(self, on_success, on_failure):
        on_success = on_success or (lambda: None)
        on_failure = on_failure or (lambda: None)
        def handler(session, response):
            if response is None:
                self.chat("Did that work? I timed out for a moment there")
                return
            error = response.getTag('error')
            if error is None:
                on_success()
                return
            not_allowed = error.getTag('not-allowed')
            if not_allowed is not None:
                self.chat("I'm sorry, Dave. I'm afraid I can't do that.")
                on_failure()
                return
            text = error.getTag('text')
            if text is None:
                self.chat('Something\'s fucky...')
                on_failure()
                return
            self.chat(str(text))
            on_failure()
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
    def banlist(self, message):
        """List the current bans. Requires admin"""
        return self.listbans(message)

    @botcmd
    @logerrors
    def listbans(self, message):
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
    def ban(self, message):
        '''bans user. Requires admin and a reason

        nick can be wrapped in single or double quotes'''

        nick, reason = self.get_nick_reason(message.args)

        if not self.nick_is_mod(message.sender_nick):
            return "nooope"
        if not len(reason):
            return "A reason must be provided"

        log.debug("trying to ban "+nick+" with reason "+reason)
        self._kickban(self.chatroom, nick, None, 'Banned by '+message.sender_nick +
                    ': ['+reason+'] at '+datetime.now().strftime("%I:%M%p on %B %d, %Y"),
                      kickban_type=self._ban)

    @botcmd(name='unban')
    @logerrors
    def un(self, message):
        '''unbans a user. Requires admin and a jid (check listbans)

        nick can be wrapped in single or double quotes'''

        jid = message.args

        if self.nick_is_mod(message.sender_nick):
            log.debug("trying to unban "+jid)
            self._kickban(self.chatroom, jid=jid, kickban_type=self._unban)
        else:
            return "noooooooope."

    @botcmd(name='kick')
    @logerrors
    def remove(self, message):
        '''kicks user. Requires admin and a reason

        nick can be wrapped in single or double quotes'''

        nick, reason = self.get_nick_reason(message.args)

        if not self.nick_is_mod(message.sender_nick):
            return "noooooooope."

        log.debug("trying to kick "+nick+" with reason "+reason)
        self._kickban(self.chatroom, nick=nick, reason=reason,
                      kickban_type=self._kick)

    def kick(self, nick, reason, on_success=None, on_failure=None):
        self._kickban(self.chatroom, nick=nick, reason=reason,
                      kickban_type=self._kick, on_success=on_success,
                      on_failure=on_failure)

    def kick_jid(self, jid, reason, on_success=None, on_failure=None):
        self._kickban(self.chatroom, jid=jid, reason=reason,
                      kickban_type=self._kick, on_success=on_success,
                      on_failure=on_failure)

    @botcmd
    @logerrors
    def sudo(self, message):
        return message.sender_nick + " is not in the sudoers file. This "+\
                "incident will be reported."

    #@botcmd()
    #@logerrors
    #def debug(self, message):
    #    # what could possibly go wrong
    #    return str(eval(message.args))
