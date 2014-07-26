import logging
from utils import logerrors, randomstr, botcmd
import re
from datetime import datetime
from sleekxmpp import Iq
import xml.etree.ElementTree as ET

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

    def message_is_from_mod(self, message):
        return message.user_jid in self.mods

    QUERY_NS = 'http://jabber.org/protocol/muc#admin'

    @staticmethod
    def query_element():
        ele = ET.Element('{'+SweetieAdmin.QUERY_NS+'}query')
        return ele

    @staticmethod
    def iq_for_kickban(room, nick, jid, reason, kickban_type):
        query = SweetieAdmin.query_element()
        item = ET.SubElement(query, 'item')
        if nick is not None:
            item.set('nick', nick)
        if jid is not None:
            item.set('jid', jid)

        if kickban_type is SweetieAdmin._kick:
            item.set('role', 'none')
        if kickban_type is SweetieAdmin._ban:
            item.set('affiliation', 'outcast')
        if kickban_type is SweetieAdmin._unban:
            item.set('affiliation', 'none')

        if reason is not None:
            item.setTagData('reason', reason)
        iq = Iq(xml=query)
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
        self.bot.send_groupchat_message(message)

    @botcmd
    def banlist(self, message):
        """List the current bans. Requires admin"""
        return self.listbans(message)

    @botcmd
    @logerrors
    def listbans(self, message):
        """List the current bans. Requires admin"""
        print('banlist')
        id = 'banlist'+randomstr()
        query = SweetieAdmin.query_element()
        item = ET.SubElement(query, 'item')
        item.set('affiliation', 'outcast')
        iq = self.bot.create_iq(id, 'get', query)

        @logerrors
        def handleBanlist(response):
            print('handleBanlist')
            print(response)
            if response is None:
                return "timed out waiting for banlist"
            res = ""
            items = response.findall('.//{'+self.QUERY_NS+'}item')
            print('items: '+str(items))
            for item in items:
                if item.get('jid') is not None:
                    res += "\n" + item.get('jid') + ": "+str(item[0].text)
            self.chat(res)

        print('created iq {}'.format(iq))

        iq.send(callback=handleBanlist)

    @botcmd(name='ban')
    @logerrors
    def ban(self, message):
        '''bans user. Requires admin and a reason

        nick can be wrapped in single or double quotes'''

        nick, reason = self.get_nick_reason(message.args)

        if not message.user_jid in self.mods:
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

        if message.user_jid in self.mods:
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

        if message.user_jid not in self.mods:
            log.debug('failing kick because {} is not registered as a mod'.format(message.sender_nick))
            return "noooooooope."

        log.debug("trying to kick "+nick+" with reason "+reason)
        self._kickban(self.chatroom, nick=nick, reason=reason,
                      kickban_type=self._kick)

    def kick(self, nick, reason, on_success=None, on_failure=None):
        self._kickban(self.chatroom, nick=nick, reason=reason,
                      kickban_type=self._kick, on_success=on_success,
                      on_failure=on_failure)

    def kick_jid(self, jid, reason, on_success=None, on_failure=None):
        nick = self.bot.get_nick_from_jid(jid)
        if nick is None:
            self.bot.chat('Could not find nick matching '+jid)
            return
        self._kickban(self.chatroom, nick=nick, reason=reason,
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
