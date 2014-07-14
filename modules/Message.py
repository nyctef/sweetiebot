
class Message(object):
    def __init__(self, nickname, sender_nick, sender_jid, message_text, message_html):
        self.nickname = nickname
        self.sender_nick = sender_nick
        self.sender_jid = sender_jid
        self.message_text = message_text
        self.message_html = message_html
        if self._is_command(nickname, message_text):
            self.command, self.args = self._get_command_and_args(message_text)
        else:
            self.command, self.args = None,None
        self.is_ping = self._is_ping(nickname, message_text)

    # TODO: make these methods consistent

    def _is_ping(self, nickname, message):
        return nickname.lower() in message.lower()

    def _get_command_and_args(self, message_text):
        if ' ' in message_text:
            return self._fix_ping(message_text).split(' ', 1)
        else:
            return message_text, ''

    def _is_command(self, nickname, message):
        return message.lower().strip().startswith(nickname.lower())

    def _fix_ping(self, message):
        message = message.strip()
        if message.lower().startswith(self.nickname.lower()):
            message = message[len(self.nickname):]
        message = message.strip()
        if message.startswith(':') or message.startswith(','):
            message = message[1:]
        return message.strip()
