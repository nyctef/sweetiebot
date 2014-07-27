import logging
from utils import logerrors, randomstr, botcmd
import re
from datetime import datetime
from sleekxmpp.exceptions import IqError, IqTimeout
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

    def set_affiliation(self, jid=None, nick=None, affiliation=None, reason=None,
            on_success=None, on_failure=None):
        """ Change room affiliation."""
        if affiliation not in ('outcast', 'member', 'admin', 'owner', 'none'):
            raise TypeError
        query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
        if nick is not None:
            item = ET.Element('{http://jabber.org/protocol/muc#admin}item', {'affiliation':affiliation, 'nick':nick})
        else:
            item = ET.Element('{http://jabber.org/protocol/muc#admin}item', {'affiliation':affiliation, 'jid':jid})
        query.append(item)
        if reason is not None:
            r = ET.Element('{http://jabber.org/protocol/muc#admin}reason')
            r.text = reason
            item.append(r)
        id = 'setaffil'+randomstr()
        iq = self.bot.create_iq(id, 'set', query)

        try:
            iq.send()
            if on_success is not None: on_success()
        except IqError as iqe:
            if on_failure is not None: on_failure()
            return iqe.text
        except IqTimeout:
            if on_failure is not None: on_failure()
            return 'did that work? I timed out for a moment there'
        return None

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

        full_reason = 'Banned by '+message.sender_nick + ': ['+reason+'] at '+datetime.now().strftime("%I:%M%p on %B %d, %Y")

        log.debug("trying to ban "+nick+" with reason "+reason)
        return self.set_affiliation(nick=nick, affiliation='outcast', reason=full_reason)

    @botcmd(name='unban')
    @logerrors
    def un(self, message):
        '''unbans a user. Requires admin and a jid (check listbans)

        nick can be wrapped in single or double quotes'''

        jid = message.args

        if message.user_jid in self.mods:
            log.debug("trying to unban "+jid)
            return self.set_affiliation(jid=jid, affiliation='none')
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

        return self.set_affiliation(nick=nick, affiliation='none', reason=reason)

    def kick(self, nick, reason, on_success=None, on_failure=None):
        return self.set_affiliation(nick=nick, reason=reason, affiliation='none',
                on_success=on_success, on_failure=on_failure)

    def kick_jid(self, jid, reason, on_success=None, on_failure=None):
        return self.set_affiliation(jid=jid, reason=reason, on_success=on_success,
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
