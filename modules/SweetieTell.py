from utils import botcmd, logerrors
from sleekxmpp import JID
from datetime import datetime
import logging
import re
from pprint import pprint

log = logging.getLogger(__name__)


class TellStorageRedis(object):
    def __init__(self, store):
        self.store = store

    def _dec(self, bytes):
        return bytes.decode("utf-8")

    def get_jid_from_nick(self, nick):
        result = self.store.get(f"jidfornick:{nick}")
        if result:
            return self._dec(result)

    def set_jid_for_nick(self, nick, jid):
        self.store.set(f"jidfornick:{nick}", str(jid))

    def set_or_update_message(self, jid, senderjid, message):
        self.store.hset(f"tell:{jid}", str(senderjid), message)

    def get_existing_messages_by_sender(self, jid):
        messages = self.store.hgetall(f"tell:{jid}")
        return {self._dec(k): self._dec(v) for (k, v) in messages.items()}

    def clear_messages_for(self, jid):
        self.store.delete(f"tell:{jid}")


class TellStoragePg(object):
    def __init__(self, conn):
        self.cur = conn.cursor()

    def get_jid_from_nick(self, nick):
        self.cur.execute(
            "SELECT jid from tell_jid_to_nick_mapping WHERE nick = %s", (nick,)
        )
        result = self.cur.fetchone()
        return result[0] if result is not None else None

    def set_jid_for_nick(self, nick, jid):
        self.cur.execute(
            "INSERT INTO tell_jid_to_nick_mapping (nick, jid) VALUES (%s, %s) "
            "ON CONFLICT (nick) DO UPDATE SET jid = EXCLUDED.jid",
            (nick, str(jid)),
        )
        self.cur.connection.commit()

    def set_or_update_message(self, jid, senderjid, message):
        self.cur.execute(
            "INSERT INTO tell_messages_by_sender (sender_jid, receiver_jid, messages) VALUES (%s, %s, %s) "
            "ON CONFLICT (sender_jid, receiver_jid) DO UPDATE SET "
            "messages = EXCLUDED.messages",
            (str(senderjid), str(jid), [message]),
        )
        self.cur.connection.commit()

    def get_existing_messages_by_sender(self, jid):
        self.cur.execute(
            "SELECT sender_jid, messages from tell_messages_by_sender "
            "WHERE receiver_jid = %s",
            (str(jid),),
        )
        results = self.cur.fetchall()
        return {s: "\n".join(m) for (s, m) in results}

    def clear_messages_for(self, jid):
        self.cur.execute(
            "DELETE FROM tell_messages_by_sender WHERE receiver_jid = %s", (str(jid),)
        )
        self.cur.connection.commit()


class SweetieTell(object):
    def __init__(self, bot, storage):
        self.storage = storage
        self.bot = bot
        self.bot.load_commands_from(self)
        self.nicktojid = NickToJidTracker(self.bot, self.storage)

    @botcmd
    def tell(self, message):
        """[user] [message] Notify a user the next time they speak in chat"""
        if message.is_pm:
            return "Sorry, you can't use !tell in a PM"
        if not message.nick_reason:
            return "A target user and message are required"
        sender_nick = message.sender_nick
        sendee_nick, mess = message.nick_reason
        if not mess:
            return "A message is required"
        sendee_jid = self.bot.get_jid_from_nick(sendee_nick)
        sendee_jid = sendee_jid or self.nicktojid.get_jid_from_nick(sendee_nick)
        sender_jid = message.user_jid
        log.debug(
            "sender_nick {} sendee_nick {} mess {} sendee_jid {} sender_jid {}".format(
                sender_nick, sendee_nick, mess, sendee_jid, sender_jid
            )
        )

        if sendee_nick == message.nickname:
            return "I'm right here, you know"
        if sendee_jid is None:
            return "Sorry, I don't know who '{}' is".format(sendee_nick)
        if sender_jid is None:
            return "I can't figure out who you are: is this channel hiding JIDs?"
        if sender_jid == sendee_jid:
            return "Talking to yourself is more efficient in real life than on jabber"
        if len(mess) > 1000:
            return "Sorry, that message is too long (1000 char maximum)"

        existing_messages = self.storage.get_existing_messages_by_sender(sendee_jid)
        existing_message = existing_messages.get(sender_jid, None)
        if existing_message is not None:
            combined_message = existing_message + "\n" + mess
            if len(combined_message) > 1000:
                return "Sorry, that message is too long (1000 char maximum; you've already used ~{})".format(
                    len(existing_message)
                )
            self.storage.set_or_update_message(sendee_jid, sender_jid, combined_message)
            return "Message received for {} (appended to previous message)".format(
                sendee_jid
            )
        if sendee_nick and mess:
            self.storage.set_or_update_message(
                sendee_jid,
                sender_jid,
                "{} left you a message: {}".format(sender_nick, mess),
            )
            return "Message received for {}".format(sendee_jid)

    def get_messages_for(self, message):
        messages = self.storage.get_existing_messages_by_sender(
            message.user_jid
        ).values()
        if len(messages):
            self.storage.clear_messages_for(message.user_jid)
            return message.sender_nick + ", " + "\n".join(messages)


class NickToJidTracker(object):
    def __init__(self, bot, storage):
        self.storage = storage
        self.bot = bot
        self.bot.add_presence_handler(self.on_presence)

    def on_presence(self, presence):
        nick = presence.muc_jid.resource
        jid = presence.user_jid.bare
        log.debug("setting jid for nick {} to {}".format(nick, jid))
        self.storage.set_jid_for_nick(nick, jid)

    def get_jid_from_nick(self, nick):
        return self.storage.get_jid_from_nick(nick)
