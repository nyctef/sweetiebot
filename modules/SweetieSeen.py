from utils import botcmd, logerrors
from sleekxmpp import JID
from datetime import datetime, timezone
import logging
from collections import namedtuple
import laboratory
from pprint import pformat

log = logging.getLogger(__name__)


class LoggingExperiment(laboratory.Experiment):
    def publish(self, result):
        if not result.match:
            logging.error("Result mismatch!: " + pformat(result))


SeenResult = namedtuple("SeenResult", ["seen", "spoke"])


class SeenStorageRedis:
    def __init__(self, store):
        self.store = store
        self.date_format = "%Y-%m-%d %H:%M"

    def _set(self, prefix, name, response):
        if name is None or response is None:
            # TODO: find out why we hit this branch
            log.warning("skipping setting {} to {}".format(name, response))
            return
        log.debug("setting {} {} to {}".format(prefix, name, response))
        self.store.set(prefix + ":" + name, response)

    def _parse(self, bytes):
        if bytes is None:
            return None
        return datetime.strptime(bytes.decode(), self.date_format)

    def set_last_seen_time(self, target, time):
        self._set("seen", target, time.strftime(self.date_format))

    def set_last_spoke_time(self, target, time):
        self._set("spoke", target, time.strftime(self.date_format))

    def get_seen(self, target):
        seen = self.store.get("seen:" + target)
        spoke = self.store.get("spoke:" + target)
        return SeenResult(self._parse(seen), self._parse(spoke))


class SeenStoragePg:
    def __init__(self, dbwrapper):
        self.dbwrapper = dbwrapper

    def set_last_seen_time(self, target, time):
        if target is None or time is None:
            # TODO: find out why we hit this branch
            log.warning("skipping setting seen {} to {}".format(target, time))
            return

        self.dbwrapper.write(
            "INSERT INTO seen_records(target, seen) VALUES "
            "(%s, %s) ON CONFLICT (target) DO UPDATE SET "
            "seen = EXCLUDED.seen",
            (target, time),
        )

    def set_last_spoke_time(self, target, time):
        if target is None or time is None:
            # TODO: find out why we hit this branch
            log.warning("skipping setting spoke {} to {}".format(target, time))
            return

        self.dbwrapper.write(
            "INSERT INTO seen_records(target, spoke) VALUES "
            "(%s, %s) ON CONFLICT (target) DO UPDATE SET "
            "spoke = EXCLUDED.spoke",
            (target, time),
        )

    def get_seen(self, target):
        result = self.dbwrapper.query_all(
            "SELECT seen, spoke from seen_records " "WHERE target = %s", (target,)
        )
        if not result:
            return SeenResult(None, None)

        (seen, spoke) = result[0]

        # round to nearest minute
        if seen is not None:
            seen = seen.replace(microsecond=0, second=0)
        if spoke is not None:
            spoke = spoke.replace(microsecond=0, second=0)
        return SeenResult(seen, spoke)


class SweetieSeen:
    def __init__(self, bot, storage):
        self.bot = bot
        self.storage = storage
        self.bot.add_presence_handler(self.on_presence)
        self.bot.add_message_handler(self.on_message)
        self.bot.load_commands_from(self)

    def on_presence(self, presence):
        log.debug(
            "recieved presence: {} from {}".format(
                presence.presence_type, presence.user_jid
            )
        )
        user = presence.user_jid.bare
        nickname = presence.muc_jid.resource
        if presence.presence_type == "unavailable":
            # record last-seen data when the target leaves the room
            self.storage.set_last_seen_time(user, datetime.now(timezone.utc))
            self.storage.set_last_seen_time(nickname, datetime.now(timezone.utc))

    def on_message(self, message):
        if message.is_pm:
            return

        nickname = message.sender_nick
        user = message.user_jid.bare
        self.storage.set_last_spoke_time(nickname, datetime.now(timezone.utc))
        self.storage.set_last_spoke_time(user, datetime.now(timezone.utc))

    @botcmd
    @logerrors
    def seen(self, message):
        """[nick/jid] Report when a user was last seen"""

        # TODO: I'm not totally convinced about the logic around jidtarget/
        # other if statements below.
        args = message.args
        jidtarget = JID(self.bot.get_jid_from_nick(args)).bare
        target = jidtarget or args

        result = self.storage.get_seen(target)
        seen = result.seen
        spoke = result.spoke

        now = datetime.now()

        if jidtarget and self.bot.jid_is_in_room(jidtarget) and spoke:
            ago = self.get_time_ago(now, spoke)
            return "{} last seen speaking at {} ({})".format(args, spoke, ago)
        elif seen:
            ago = self.get_time_ago(now, seen)
            return "{} last seen in room at {} ({})".format(args, seen, ago)
        else:
            return "No records found for user '{}'".format(args)

    def get_time_ago(self, now, past):
        td = now - past
        if td.total_seconds() < 0:
            return "in the future"
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return "{}d {}h {}m {}s ago".format(days, hours, minutes, seconds)
