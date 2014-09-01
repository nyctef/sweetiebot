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

    def set(self, prefix, name, response):
        if name is None or response is None:
            # TODO: find out why we hit this branch
            log.warning('skipping setting {} to {}'.format(name, response))
            return
        log.debug('setting {} {} to {}'.format(prefix, name, response))
        self.store.set(prefix+':'+name, response)

    def on_presence(self, presence):
        log.debug('recieved presence: {} from {}'.format(presence.presence_type,
                                                         presence.user_jid))
        user = presence.user_jid.bare
        nickname = presence.muc_jid.resource
        if presence.presence_type == 'unavailable':
            response = self.timestamp()
            self.set('seen', user, response)
            self.set('seen', nickname, response)

    def on_message(self, message):
        if message.is_pm: return

        response = self.timestamp()
        nickname = message.sender_nick
        user = message.user_jid.bare
        self.set('spoke', nickname, response)
        self.set('spoke', user, response)

    @botcmd
    @logerrors
    def seen(self, message):
        '''[nick/jid] Report when a user was last seen'''

        # TODO: I'm not totally convinced about the logic around jidtarget/
        # other if statements below.
        args = message.args
        jidtarget = JID(self.bot.get_jid_from_nick(args)).bare
        target = jidtarget or args

        seen = self.store.get('seen:'+target)
        spoke = self.store.get('spoke:'+target)

        if jidtarget and self.bot.jid_is_in_room(jidtarget) and spoke:
            spoke = spoke.decode('utf-8')
            return '{} last seen speaking at {}'.format(args, spoke)
        elif seen:
            seen = seen.decode('utf-8')
            return '{} last seen in room at {}'.format(args, seen)
        else:
            return "No records found for user '{}'".format(args)


