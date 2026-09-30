import logging
import re
from slixmpp import JID
from modules.RoomMember import RoomMemberList

log = logging.getLogger(__name__)


class Message(object):

    prefix = "!"

    def __init__(
        self,
        nickname: str,
        sender_nick: str | None,
        sender_jid: JID | str,
        user_jid: JID | str,
        message_text: str,
        is_pm: bool,
        room_member_list: RoomMemberList,
    ) -> None:
        self.nickname = nickname
        self.sender_nick = sender_nick
        self.sender_jid = JID(sender_jid)
        self.user_jid = JID(user_jid)
        self.message_text = message_text
        self.is_pm = is_pm
        self.room_member_list = room_member_list
        self.command: str | None
        self.args: str | None
        self.nick_reason: tuple[str, str] | None

        if self._is_command(nickname, message_text) or is_pm:
            self.command, self.args = self._get_command_and_args(message_text)
            self.nick_reason = self._get_nick_reason(self.args)
        else:
            self.command, self.args, self.nick_reason = None, None, None
        self.is_ping = self._is_ping(nickname, message_text) or is_pm
        log.debug(
            """creating message:
        self: {}
        sender: {} jid {} user {}
        message: {}
        parsed: {}|{}
        is_ping: {}""".format(
                self.nickname,
                self.sender_nick,
                self.sender_jid,
                self.user_jid,
                self.message_text,
                self.command,
                self.args,
                self.is_ping,
            )
        )
        log.debug("room list: %r", self.room_member_list)
        log.info("{}: {}".format(self.sender_nick, self.message_text))

    def _is_ping(self, nickname: str, message: str) -> bool:
        return nickname.lower() in message.lower()

    def _get_command_and_args(self, message_text: str) -> tuple[str, str]:
        message_after_ping = self._fix_ping(message_text)
        if " " in message_after_ping:
            command, args = [x.strip() for x in message_after_ping.split(None, 1)]
        else:
            command, args = message_after_ping, ""

        if command.startswith(self.prefix):
            command = command[1:]
        command = command.lower()

        return command, args

    def _is_command(self, nickname: str, message: str) -> bool:
        return message.lower().strip().startswith(
            nickname.lower()
        ) or message.startswith(self.prefix)

    def _fix_ping(self, message: str) -> str:
        message = message.strip()
        if message.lower().startswith(self.nickname.lower()):
            message = message[len(self.nickname):]
        message = message.strip()
        if message.startswith(":") or message.startswith(","):
            message = message[1:]
        return message.strip()

    def _get_nick_reason(self, args: str) -> tuple[str, str] | None:
        if not args:
            return None

        known_nicks = self.room_member_list.get_nick_list()
        re_options = re.IGNORECASE | re.DOTALL
        nick: str | None
        reason: str | None
        for known_nick in known_nicks:
            # re.match only matches the start of the string
            match = (
                re.match(r"\s*'" + known_nick + "'(.*)", args, re_options)
                or re.match(r'\s*"' + known_nick + '"(.*)', args, re_options)
                or re.match(r"\s*" + known_nick + "(.*)", args, re_options)
            )
            if match:
                nick = known_nick
                reason = match.group(1).strip()
                return nick, reason

        nick = None
        reason = None
        match = (
            re.match(r"\s*'([^']*)'(.*)", args, re_options)
            or re.match(r'\s*"([^"]*)"(.*)', args, re_options)
            or re.match(r"\s*(\S*)(.*)", args, re_options)
        )
        if match:
            nick = match.group(1)
            reason = match.group(2).strip()
        # the last pattern above always matches, so nick and reason are always set
        return nick, reason  # type: ignore[return-value]

    def sender_can_do_admin_things(self) -> bool:
        member = self.room_member_list.get_member_from_nickname(self.sender_nick)
        return member is not None and member.can_do_admin_things()
