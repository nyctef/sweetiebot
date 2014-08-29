from utils import botcmd, logerrors
from sleekxmpp import JID
from datetime import datetime
import logging

log = logging.getLogger(__name__)

class SweetieSeen:
    def __init__(self, bot, store):
        self.bot = bot
        self.store = store
        self.bot.add_presence_handler(self.on_presence)
        self.bot.add_message_handler(self.on_message)
        self.bot.load_commands_from(self)

    def timestamp(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M %Z')

    def set(self, name, response):
        if name is None or response is None:
            # TODO: find out why we hit this branch
            log.debug('skipping setting {} to {}'.format(name, response))
            return
        log.debug('setting {} to {}'.format(name, response))
        self.store.set('seen:'+name, response)

    def on_presence(self, presence):
        log.debug('recieved presence: {} from {}'.format(presence.presence_type,
                                                         presence.user_jid))
        if presence.presence_type == 'unavailable':
            response = 'leaving the room at {}'.format(self.timestamp())
            self.set(presence.muc_jid.resource, response)
            self.set(presence.user_jid.bare, response)

    def on_message(self, message):
        response = 'chatting at {}'.format(self.timestamp())
        self.set(message.sender_nick, response)
        self.set(message.sender_jid.bare, response)

    @botcmd
    @logerrors
    def seen(self, message):
        '''[nick/jid] Report when a user was last seen'''
        target = message.args
        jidtarget = JID(self.bot.get_jid_from_nick(target)).bare or target

        response = self.store.get('seen:'+target) or \
            self.store.get('seen:'+jidtarget)
        if response:
            response = response.decode('utf-8')
            return 'User {} last seen {}'.format(target, response)
        else:
            return 'No records found for user {}'.format(target)

