from jabberbot import JabberBot
import utils
import re
import xmpp
import logging

log = logging.getLogger(__name__)

class RestartException(Exception):
    pass

class MUCJabberBot(JabberBot):

    flood_protection = 0
    flood_delay = 5
    PING_FREQUENCY = 60
    nicks_to_jids = {}

    def __init__(self, nickname, *args, **kwargs):
        ''' Initialize variables. '''

        # answer only direct messages or not?
        self.nickname = nickname
        self.only_direct = kwargs.get('only_direct', False)

        try:
            del kwargs['only_direct']
        except KeyError:
            pass

        # initialize jabberbot
        super(MUCJabberBot, self).__init__(*args, **kwargs)

        # create a regex to check if a message is a direct message
        user, domain = str(self.jid).split('@')
        self.direct_message_re = re.compile('^%s(@%s)?[^\w]? '
                                            % (user, domain))

        self.unknown_command_callback = None


    def callback_message(self, conn, mess):
        ''' Changes the behaviour of the JabberBot in order to allow
        it to answer direct messages. This is used often when it is
        connected in MUCs (multiple users chatroom). '''
        # fuck you unicode
        message = mess.getBody()
        props = mess.getProperties()
        jid = mess.getFrom()
        try:
            if self.direct_message_re.match(message):
                mess.setBody(' '.join(message.split(' ', 1)[1:]))
                super(MUCJabberBot, self).callback_message(conn, mess)
        except TypeError as e:
            log.debug('random typeerror: '+str(e))
            return
        if not message:
            return
        if xmpp.NS_DELAY in props:
            return

        log.debug('comparing jid {} against message from {}'.format(
            self.jid, jid))
        if self.jid.bareMatch(jid):
            log.debug('ignoring from jid')
            return
        if self.get_sender_username(mess) == self.nickname:
            log.debug('ignoring from nickname')
            return

        if mess.getSubject():
            log.debug('ignoring subject..')
            return

        if utils.is_command(self.nickname, message):
            message = self.fix_ping(message)
            log.debug('fixed message: '+message)

            command, args = self.get_command_and_args(message)

            command = command.lower()
            if command in self.commands:
                mess.setBody(message)
                super(MUCJabberBot, self).callback_message(conn, mess)
                return
        command, args = self.get_command_and_args(message)
        reply = self.unknown_command(mess, command, args)
        if reply:
            log.debug('sending reply: '+reply)
            self.send_simple_reply(mess, reply)

    def get_command_and_args(self, message):
        if ' ' in message:
            return message.split(' ', 1)
        else:
            return message, ''

    def callback_presence(self, conn, presence):
        super(MUCJabberBot, self).callback_presence(conn, presence)
        nick = presence.getFrom().getResource()
        if presence.getJid() is not None:
            self.nicks_to_jids[nick] = xmpp.JID(presence.getJid()).getStripped()

    def get_jid_from_nick(self, nick):
        if self.nicks_to_jids.has_key(nick): return self.nicks_to_jids[nick]

    def load_commands_from(self, target):
        import inspect
        for name, value in inspect.getmembers(target, inspect.ismethod):
            if getattr(value, '_jabberbot_command', False):
                name = getattr(value, '_jabberbot_command_name')
                self.log.info('Registered command: %s' % name)
                self.commands[name] = value

    def fix_ping(self, message):
        message = message.strip()
        if message.lower().startswith(self.nickname.lower()):
            message = message[len(self.nickname):]
        message = message.strip()
        if message.startswith(':') or message.startswith(','):
            message = message[1:]
        return message.strip()

    def unknown_command(self, mess, cmd, args):
        if self.unknown_command_callback is not None:
            return self.unknown_command_callback(self, mess, cmd, args)

    def on_ping_timeout(self):
        log.error('ping timeout.')
        raise RestartException()

    def send_iq(self, iq, callback=None):
        if callback is not None:
            self.connect().SendAndCallForResponse(iq, callback)
        else:
            self.connect().send(iq)

