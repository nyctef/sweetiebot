from modules.Message import Message
from modules.MessageResponse import MessageResponse
from modules.MessageProcessor import MessageProcessor
import logging
from utils import logerrors
from sleekxmpp import ClientXMPP
from sleekxmpp.xmlstream.jid import JID
import html

log = logging.getLogger(__name__)

class RestartException(Exception):
    pass

class MUCJabberBot():

    def __init__(self, jid, password, room, nick):
        print('creating bot with {} {} {} {} '.format(jid, password, room, nick))
        self.nick = nick
        self.room = room
        self.jid = JID(jid)

        bot = ClientXMPP(jid, password)

        bot.add_event_handler('session_start', self.on_start)
        bot.add_event_handler('message', self.on_message)

        bot.register_plugin('xep_0045')
        self._muc = bot.plugin['xep_0045']
        bot.register_plugin('xep_0199')
        bot.plugin['xep_0199'].enable_keepalive(30, 30)

        self.unknown_command_callback = None

        def on_unknown_callback(message):
            if self.unknown_command_callback is not None:
                return self.unknown_command_callback(message)
        self.message_processor = MessageProcessor(on_unknown_callback)

        print('sb connect')
        if bot.connect():
            print('sb process')
            bot.process()
        else:
            raise 'could not connect'

        self._bot = bot

    def disconnect(self):
        self._bot.disconnect()

    def on_start(self, event):
        print('sb on_start')
        self._bot.get_roster()
        self._bot.send_presence()
        print('sb join {} as {}'.format(self.room, self.nick))
        self._muc.joinMUC(self.room, self.nick, wait=True)

    @logerrors
    def on_message(self, message_stanza):

        if message_stanza['type'] == 'error':
            print('\n\nerror!\n\n')
            log.error(message_stanza)

        body = message_stanza['body']
        if not body:
            log.warn('apparently empty message [no body] %s', message_stanza)
            return

        #print('##')
        #print('keys: {}'.format(message_stanza.keys()))
        #print('xml: {}'.format(message_stanza.xml))
        #print('type: {}'.format(message_stanza['type']))

        #props = mess.getProperties()
        jid = message_stanza['from']

#        if xmpp.NS_DELAY in props:
#            # delayed messages are history from before we joined the chat
#            return

        log.debug('comparing jid {} against message from {}'.format(
            self.jid, jid))
        if self.jid.bare == jid.bare:
            log.debug('ignoring from jid')
            return

        #print('checking for subject {}'.format(message_stanza['subject']))
        if message_stanza['subject']:
            log.debug('ignoring subject..')
            return

        if message_stanza['mucnick']:
            sender_nick = message_stanza['mucnick']
            user_jid = self.get_jid_from_nick(sender_nick)
        else:
            user_jid = jid
            sender_nick = self.get_nick_from_jid(user_jid)
        user_jid = JID(user_jid).bare

        if sender_nick == self.nick:
            log.debug('ignoring from nickname')
            return

        is_pm = message_stanza['type'] == 'chat'
        message_html = str(message_stanza['html']['body'])
        message = message_stanza['body']
        parsed_message = Message(self.nick, sender_nick, jid, user_jid, message,
                                 message_html, is_pm)

        reply = self.message_processor.process_message(parsed_message)
        if reply:
            if is_pm: self.send_chat_message(reply, jid)
            else: self.send_groupchat_message(reply)

    def send_chat_message(self, message, jid):
        self.send_message(message, jid, 'chat')

    def send_groupchat_message(self, message):
        self.send_message(message, self.room, 'groupchat')

    def send_message(self, message, default_destination, mtype):
        message = MessageResponse(message, default_destination)
        self._bot.send_message(mto=message.destination,
                               mbody=message.plain,
                               mhtml=message.html,
                               mtype=mtype)

    def get_jid_from_nick(self, nick):
        return self._muc.getJidProperty(self.room, nick, 'jid').bare

    def get_nick_from_jid(self, jid):
        # sleekxmpp has a method for this but it uses full jids
        room_details = self._muc.rooms[self.room]
        log.debug('room details '+str(room_details))
        for nick, props in room_details.items():
            if JID(props['jid']).bare == JID(jid).bare:
                return nick

    def load_commands_from(self, target):
        import inspect
        for name, value in inspect.getmembers(target, inspect.ismethod):
            if getattr(value, '_bot_command', False):
                name = getattr(value, '_bot_command_name')
                log.info('Registered command: %s' % name)
                self.message_processor.add_command(name, value)

    def on_ping_timeout(self):
        log.error('ping timeout.')
        raise RestartException()

    def create_iq(self, id, type, xml):
        iq = self._bot.make_iq(id=id, ifrom=self.jid, ito=self.room, itype=type)
        iq.set_payload(xml)
        return iq

    def add_recurring_task(self, callback, secs):
        self._bot.scheduler.add('custom task '+callback.__name__, secs,
                                callback, repeat=True)

