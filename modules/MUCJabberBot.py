from jabberbot import JabberBot
from Message import Message
import re
import xmpp
import logging

log = logging.getLogger(__name__)

class RestartException(Exception):
    pass

class MessageProcessor(object):

    def __init__(self, unknown_command_callback):
        self.commands = {}
        self.unknown_command_callback = unknown_command_callback

    def add_command(self, command_name, command_callback):
        self.commands[command_name] = command_callback

    def process_message(self, message):
        if message.command is not None:
            if message.command in self.commands:
                log('running command '+message.command)
                return self.commands[message.command](message)

        if self.unknown_command_callback is not None:
            return self.unknown_command_callback(message)

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

        def on_unknown_callback(message):
            if self.unknown_command_callback is not None:
                return self.unknown_command_callback(message)
        self.message_processor = MessageProcessor(on_unknown_callback)

    def callback_message(self, conn, mess):
        message = mess.getBody()
        if not message:
            log.warn('apparently empty message %s', mess)
            return

        props = mess.getProperties()
        jid = mess.getFrom()
        if self.direct_message_re.match(message):
            self.deal_with_direct_message(mess)

        if xmpp.NS_DELAY in props:
            # delayed messages are history from before we joined the chat
            return

        log.debug('comparing jid {} against message from {}'.format(
            self.jid, jid))
        if self.jid.bareMatch(jid):
            log.debug('ignoring from jid')
            return

        sender_nick = self.get_sender_username(mess)
        if sender_nick == self.nickname:
            log.debug('ignoring from nickname')
            return

        if mess.getSubject():
            log.debug('ignoring subject..')
            return

        parsed_message = Message(self.nickname, sender_nick, jid, message,
                                 message) # TODO message_html

        reply = self.message_processor.process_message(parsed_message)
        log.debug('reply: '+str(reply))
        if reply:
            self.send_simple_reply(mess, reply)

    def deal_with_direct_message(self, mess):
        pass

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
                log.info('Registered command: %s' % name)
                self.message_processor.add_command(name, value)

    def on_ping_timeout(self):
        log.error('ping timeout.')
        raise RestartException()

    def send_iq(self, iq, callback=None):
        if callback is not None:
            self.connect().SendAndCallForResponse(iq, callback)
        else:
            self.connect().send(iq)

