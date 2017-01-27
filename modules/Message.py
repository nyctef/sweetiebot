import logging
from sleekxmpp import JID

log = logging.getLogger(__name__)

class Message(object):

    prefix = '!'

    def __init__(self, nickname, sender_nick, sender_jid, user_jid,\
            message_text, message_html, is_pm, room_member_list):
        self.nickname = nickname
        self.sender_nick = sender_nick
        self.sender_jid = JID(sender_jid)
        self.user_jid = JID(user_jid)
        self.message_text = message_text
        self.message_html = message_html
        self.is_pm = is_pm
        self.room_member_list = room_member_list

        if self._is_command(nickname, message_text) or is_pm:
            self.command, self.args = self._get_command_and_args(message_text)
        else:
            self.command, self.args = None,None
        self.is_ping = self._is_ping(nickname, message_text) or is_pm
        log.debug('''creating message:
        self: {}
        sender: {} jid {} user {}
        message: {}
        message_html: {}
        parsed: {}|{}
        is_ping: {}'''.format(self.nickname, self.sender_nick, self.sender_jid,
            self.user_jid, self.message_text, self.message_html, self.command, self.args,
            self.is_ping))
        log.debug('room list: %r', self.room_member_list)
        log.info('{}: {}'.format(self.sender_nick, self.message_text))

    def _is_ping(self, nickname, message):
        return nickname.lower() in message.lower()

    def _get_command_and_args(self, message_text):
        message_after_ping = self._fix_ping(message_text)
        if ' ' in message_after_ping:
            command, args = [x.strip() for x in message_after_ping.split(None, 1)]
        else:
            command, args = message_after_ping, ''

        if command.startswith(self.prefix):
            command = command[1:]
        command = command.lower()

        return command, args

    def _is_command(self, nickname, message):
        return message.lower().strip().startswith(nickname.lower()) or \
                message.startswith(self.prefix)

    def _fix_ping(self, message):
        message = message.strip()
        if message.lower().startswith(self.nickname.lower()):
            message = message[len(self.nickname):]
        message = message.strip()
        if message.startswith(':') or message.startswith(','):
            message = message[1:]
        return message.strip()

    def _get_member_from_nickname(self, nickname=self.nickname):
        result = next((x for x in self.room_member_list if x.nickname == nickname), None)
        if not result:
            log.warning("Couldn't find member entry for nickname %s", nickname)
        return result

    def sender_can_do_admin_things(self):
        member = self._get_member_from_nickname(self.sender_nick)
        return member != None and member.can_do_admin_things()
