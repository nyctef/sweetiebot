from jabberbot import JabberBot
from Message import Message
import xmpp
import logging
from utils import logerrors
import re

log = logging.getLogger(__name__)

class RestartException(Exception):
    pass

class MessageProcessor(object):

    def __init__(self, unknown_command_callback):
        self.commands = {}
        self.unknown_command_callback = unknown_command_callback

    def add_command(self, command_name, command_callback):
        self.commands[command_name] = command_callback

    @logerrors
    def process_message(self, message):
        if message.command is not None:
            if message.command in self.commands:
                log.debug('running command '+message.command)
                return self.commands[message.command](message)

        if self.unknown_command_callback is not None:
            return self.unknown_command_callback(message)

class MUCJabberBot(JabberBot):

    flood_protection = 0
    flood_delay = 5
    PING_FREQUENCY = 60
    nicks_to_jids = {}
    jids_to_nicks = {}

    def __init__(self, nickname, *args, **kwargs):
        ''' Initialize variables. '''

        self.nickname = nickname

        # initialize jabberbot
        super(MUCJabberBot, self).__init__(*args, **kwargs)

        # create a regex to check if a message is a direct message
        user, domain = str(self.jid).split('@')

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

        if xmpp.NS_DELAY in props:
            # delayed messages are history from before we joined the chat
            return

        log.debug('comparing jid {} against message from {}'.format(
            self.jid, jid))
        if self.jid.bareMatch(jid):
            log.debug('ignoring from jid')
            return

        if mess.getSubject():
            log.debug('ignoring subject..')
            return

        if self.groupchat_im_re and self.groupchat_im_re.match(str(mess.getFrom())):
            sender_nick = jid.getResource()
            user_jid = self.get_jid_from_nick(sender_nick)
        else:
            user_jid = jid.getStripped()
            sender_nick = self.get_nick_from_jid(user_jid)

        if sender_nick == self.nickname:
            log.debug('ignoring from nickname')
            return

        is_pm = mess.getAttr('type') == 'chat'
        message_html = self.get_message_html(mess)
        parsed_message = Message(self.nickname, sender_nick, jid, user_jid, message,
                                 message_html, is_pm)

        reply = self.message_processor.process_message(parsed_message)
        if reply:
            self.send_simple_reply(mess, reply, is_pm)

    def join_room(self, room, nick):
        self.room = room
        self.nick = nick
        self.groupchat_im_re = re.compile(r'{}/(\w+)'.format(room))
        super(MUCJabberBot, self).join_room(room, nick)

    def send_pm_to_jid(self, jid, pm):
        response = xmpp.Message(jid, pm)
        response.setType('chat')
        self.send_message(response)

    def get_message_html(self, xml_message):
        # simple case: no html in message
        if xml_message.getTag('html') is None:
            return xml_message.getTag('body').getData()

        #print ' dealing with '+xml_message
        # complex case: concat all children of /html/body
        nodes = xml_message.getTag('html').getTag('body').getPayload()

        return self.nodes_to_string(nodes)

    def nodes_to_string(self, nodes):
        strings = map(self.node_str, nodes)
        return ''.join(strings)

    def node_str(self, obj):
        if isinstance(obj, xmpp.simplexml.Node):
            return self.nodes_to_string(obj.getPayload())

        # we can't call on str on unicode objects so just pass them through
        if isinstance(obj, unicode):
            return obj

        return str(obj)

    def callback_presence(self, conn, presence):
        super(MUCJabberBot, self).callback_presence(conn, presence)
        nick = presence.getFrom().getResource()
        if presence.getJid() is not None:
            jid = xmpp.JID(presence.getJid()).getStripped()
            self.nicks_to_jids[nick] = jid
            self.jids_to_nicks[jid] = nick

    def get_jid_from_nick(self, nick):
        if self.nicks_to_jids.has_key(nick): return self.nicks_to_jids[nick]

    def get_nick_from_jid(self, jid):
        if self.jids_to_nicks.has_key(jid): return self.jids_to_nicks[jid]

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

