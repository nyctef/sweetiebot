import logging
from utils import logerrors, randomstr, botcmd
from datetime import datetime
from sleekxmpp.exceptions import IqError, IqTimeout
import xml.etree.ElementTree as ET

log = logging.getLogger(__name__)


class SweetieAdmin(object):
    _kick = "kick"
    _ban = "ban"
    _unban = "unban"

    def __init__(self, bot, chatroom):
        self.bot = bot
        self.bot.load_commands_from(self)
        self.chatroom = chatroom

    QUERY_NS = "http://jabber.org/protocol/muc#admin"

    @staticmethod
    def query_element():
        ele = ET.Element("{" + SweetieAdmin.QUERY_NS + "}query")
        return ele

    def chat(self, message):
        self.bot.send_groupchat_message(message)

    @botcmd(hidden=True)
    def banlist(self, message):
        """List currently-banned users"""
        return self.listbans(message)

    def set_affiliation(
        self,
        jid=None,
        nick=None,
        atype="role",
        value=None,
        reason=None,
        on_success=None,
        on_failure=None,
    ):
        """ Change room affiliation."""
        values = ("outcast", "member", "admin", "owner", "none")
        if value not in values:
            raise TypeError("value must be one of " + repr(values))
        atypes = ("role", "affiliation")
        if atype not in atypes:
            raise TypeError("atype must be one of " + repr(atypes))
        query = ET.Element("{http://jabber.org/protocol/muc#admin}query")
        if nick is not None:
            item = ET.Element(
                "{http://jabber.org/protocol/muc#admin}item",
                {atype: value, "nick": nick},
            )
        elif jid is not None:
            item = ET.Element(
                "{http://jabber.org/protocol/muc#admin}item", {atype: value, "jid": jid}
            )
        else:
            raise Exception("nick or jid needs to be set")
        query.append(item)
        if reason is not None:
            r = ET.Element("{http://jabber.org/protocol/muc#admin}reason")
            r.text = reason
            item.append(r)
        id = "setaffil" + randomstr()
        iq = self.bot.create_iq(id, "set", query)
        log.debug("created affiliation iq: " + str(iq))

        try:
            response = iq.send()
            if on_success is not None:
                on_success()
            log.debug("got affiliation response: " + str(response))
        except IqError as iqe:
            log.debug("got iqerror: " + str(iqe))
            if on_failure is not None:
                on_failure()
            if iqe.text:
                return iqe.text
            error_condition = iqe.iq["error"]["condition"]
            if error_condition:
                return "Operation failed on {}: {}".format(nick or jid, error_condition)
            return "Operation failed on {}".format(nick or jid)
        except IqTimeout:
            if on_failure is not None:
                on_failure()
            return "did that work? I timed out for a moment there"

    @botcmd
    @logerrors
    def listbans(self, message):
        """List currently-banned users"""
        id = "banlist" + randomstr()
        query = SweetieAdmin.query_element()
        item = ET.SubElement(query, "item")
        item.set("affiliation", "outcast")
        iq = self.bot.create_iq(id, "get", query)

        response = iq.send()
        res = ""
        items = response.findall(".//{" + self.QUERY_NS + "}item")
        log.debug("banlist items: " + str(items))
        for item in items:
            if item.get("jid") is not None:
                try:
                    reason = str(item[0].text)
                except Exception:
                    reason = "[reason unavailable]"
                res += "\n" + item.get("jid") + ": " + reason
        if not res:
            return "Bans list is empty"
        return res

    @botcmd
    @logerrors
    def ban(self, message):
        """[nick] [reason] Bans a user from the chat
        nick can be wrapped in quotes"""

        if not message.sender_can_do_admin_things():
            return "nooope"
        if not message.nick_reason:
            return "A nickname and reason must be provided"
        nick, reason = message.nick_reason
        if not len(reason):
            return "A reason must be provided"

        full_reason = (
            "banned by "
            + message.sender_nick
            + ": ["
            + reason
            + "] at "
            + datetime.now().strftime("%I:%M%p on %B %d, %Y")
        )

        log.debug("trying to ban " + nick + " with reason " + reason)
        return self.set_affiliation(
            nick=nick, atype="affiliation", value="outcast", reason=full_reason
        ) or (nick + " " + full_reason)

    @botcmd
    @logerrors
    def unban(self, message):
        """[jid] Unbans a user from the chat.
        Use listbans to find jids"""

        jid = message.args

        if message.sender_can_do_admin_things():
            log.debug("trying to unban " + jid)
            return self.set_affiliation(jid=jid, atype="affiliation", value="none") or (
                "cleared ban from " + jid
            )
        else:
            return "noooooooope."

    @botcmd(name="kick")
    @logerrors
    def remove(self, message):
        """[nick] [reason-optional] Kicks a user from the chat
        nick can be wrapped in quotes"""

        if not message.nick_reason:
            return "A nickname and reason must be provided"
        nick, reason = message.nick_reason

        if not message.sender_can_do_admin_things():
            log.debug(
                "failing kick because {} is not registered as a mod".format(
                    message.sender_nick
                )
            )
            return "Do you have a flag? No flag, no kick. You can't have one!"

        log.debug("trying to kick " + nick + " with reason " + reason)

        return self.set_affiliation(
            nick=nick, atype="role", value="none", reason=reason
        )

    def kick(self, nick, reason, on_success=None, on_failure=None):
        return self.set_affiliation(
            nick=nick,
            reason=reason,
            atype="role",
            value="none",
            on_success=on_success,
            on_failure=on_failure,
        )

    @botcmd(name="kickjid")
    @logerrors
    def remove_jid(self, message):
        """[jid] [reason-optional] Kicks a user by their jid from the chat"""

        if not message.nick_reason:
            return "A nickname and reason must be provided"
        jid, reason = message.nick_reason

        if not message.sender_can_do_admin_things():
            log.debug(
                "failing kick because {} is not registered as a mod".format(
                    message.sender_nick
                )
            )
            return "Do you have a flag? No flag, no kick. You can't have one!"

        log.debug("trying to kick " + jid + " with reason " + reason)

        return self.kick_jid(jid, reason)

    def kick_jid(self, jid, reason, on_success=None, on_failure=None):
        log.debug("finding nick for jid " + jid)
        nick = self.bot.get_nick_from_jid(jid)
        if nick is None:
            return "User does not appear to be in chat"
        log.debug("got nick " + nick)
        return self.set_affiliation(
            nick=nick,
            atype="role",
            value="none",
            reason=reason,
            on_success=on_success,
            on_failure=on_failure,
        )

    @botcmd
    @logerrors
    def sudo(self, message):
        """[command] Escalate privileges"""
        return (
            message.sender_nick
            + " is not in the sudoers file. This "
            + "incident will be reported."
        )

    # @botcmd()
    # @logerrors
    # def debug(self, message):
    #    # what could possibly go wrong
    #    return str(eval(message.args))
