from modules.Message import Message
from modules.MessageResponse import MessageResponse
from modules.MessageProcessor import MessageProcessor
from modules.Presence import Presence
from modules.RoomMember import RoomMember, RoomMemberList
import logging
from utils import logerrors
from sleekxmpp import ClientXMPP
from sleekxmpp.jid import JID
import html
from time import sleep
import os

log = logging.getLogger(__name__)

class RestartException(Exception):
    pass

class MUCJabberBot():
    
    def __init__(self, jid, password, room, nick, address=()):
        log.info('creating bot with {} {} {} {} {}'
                .format(jid, password, room, nick, address))
        self.nick = nick
        self.room = room
        self.jid = JID(jid)
        self._presence_callbacks = []
        self._message_callbacks = []

        bot = ClientXMPP(jid, password)

        # disable ipv6 for now since we're getting errors using it
        bot.use_ipv6 = False

	# Fix certain Jabber clients not showing messages by giving them an ID
        bot.use_message_ids = True

        # Don't try to auto reconnect after disconnections (we'll restart the
        # process and retry that way)
        bot.auto_reconnect = False

        bot.add_event_handler('session_start', self.on_start)
        bot.add_event_handler('message', self.on_message)
        bot.add_event_handler('groupchat_presence', self.on_presence)
        bot.add_event_handler('groupchat_subject', self.on_room_joined)
        bot.add_event_handler('disconnected', self.on_disconnect)

        bot.register_plugin('xep_0045')
        self._muc = bot.plugin['xep_0045']
        bot.register_plugin('xep_0199')
        bot.plugin['xep_0199'].enable_keepalive(5, 10)

        self.unknown_command_callback = None

        def on_unknown_callback(message):
            if self.unknown_command_callback is not None:
                return self.unknown_command_callback(message)
        self.message_processor = MessageProcessor(on_unknown_callback)

        log.info('sb connect')
        if bot.connect(address=address, reattempt=False):
            log.info('sb process')
            bot.process()
        else:
            log.error('failed to connect at first attempt')
            self.on_disconnect(None)

        self.add_presence_handler(self.rejoin_if_kicked)

        self._bot = bot

    def on_start(self, event):
        log.info('sb on_start')
        self._bot.get_roster()
        self._bot.send_presence(ppriority=100)
        log.info('sb join {} as {}'.format(self.room, self.nick))
        self.join_room()

    def join_room(self):
        self._muc.joinMUC(self.room, self.nick)

    def on_room_joined(self, room_join_message):
        '''Note that this event might actually be called multiple
        times due to the room name being changed. This method
        needs to be idempotent'''
        log.debug('on_room_joined with {}'.format(room_join_message))
        self._rejoining = False

    def on_disconnect(self, event):
        log.error('disconnected event raised, quitting so we can restart from scratch')
        # os._exit() actually nukes the process (instead of raising SystemExit
        # like sys.exit() does)
        os._exit(0)

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

        room_member_list = self._get_room_member_list()

        is_pm = message_stanza['type'] == 'chat'
        message_html = str(message_stanza['html']['body'])
        message = message_stanza['body']
        parsed_message = Message(self.nick, sender_nick, jid, user_jid, message,
                                 message_html, is_pm, room_member_list)

        reply = self.message_processor.process_message(parsed_message)
        if reply:
            if is_pm: self.send_chat_message(reply, jid)
            else: self.send_groupchat_message(reply)

        for callback in self._message_callbacks:
            callback(parsed_message)

    def _get_room_member_list(self):
        room_details = self._muc.rooms[self.room]
        member_list = [self._get_room_member(nick, props) \
                for (nick, props) in room_details.items()]
        return RoomMemberList(member_list)

    def _get_room_member(self, nick, props):
        return RoomMember(nick, JID(props['jid']), props['affiliation'], props['role'])

    @logerrors
    def on_presence(self, presence_stanza):
        log.debug('creating Presence from {}'.format(presence_stanza))
        muc_jid = JID(presence_stanza['from'])
        user = JID(presence_stanza['muc']['jid'])
        ptype = presence_stanza['type']
        status_text = presence_stanza['status']
        log.debug('created muc_jid={} user={} ptype={} status_text={}'.format(
            muc_jid, user, ptype, status_text))

        nick = presence_stanza['muc']['nick']

        presence = Presence(muc_jid, user, ptype, status_text)
        for callback in self._presence_callbacks:
            callback(presence)

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
        jid = self._muc.getJidProperty(self.room, nick, 'jid')
        if jid is None: return None
        return jid.bare

    def get_nick_from_jid(self, jid):
        # sleekxmpp has a method for this but it uses full jids
        room_details = self._muc.rooms[self.room]
        log.debug('room details '+str(room_details))
        for nick, props in room_details.items():
            if JID(props['jid']).bare == JID(jid).bare:
                return nick

    def jid_is_in_room(self, jid):
        return self.get_nick_from_jid(jid) is not None

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

    def add_recurring_task(self, callback, secs, repeat=True):
        task_name = 'custom task '+callback.__name__
        self._bot.scheduler.remove(task_name)
        self._bot.scheduler.add(task_name, secs, callback, repeat=repeat)

    def add_presence_handler(self, callback):
        self._presence_callbacks.append(callback)

    def add_message_handler(self, callback):
        self._message_callbacks.append(callback)

    def rejoin_if_kicked(self, presence):
        log.debug(presence)
        log.debug('recieved presence: {} from {}'.format(presence.presence_type,
                                                         presence.user_jid))
        if presence.presence_type != 'unavailable':
            return
        user = presence.user_jid.bare
        if user == self.jid.bare:
            log.debug('looks like we were kicked, rejoining...')
            self._rejoining = True
            self.rejoin()
        else:
            log.debug('{} was kicked'.format(user))

    def rejoin(self):
        if self._rejoining == False: return
        log.debug('attempting a room rejoin... (self._rejoining={})'.format(self._rejoining))
        self.join_room()
        self.add_recurring_task(self.rejoin, 5, repeat=False)

