from utils import logerrors, botcmd
from datetime import datetime
import logging
import random
import json
from sleekxmpp.xmlstream.jid import JID

log = logging.getLogger(__name__)

class SweetieDe(object):
    kick_owl_delay = 7200
    last_owl_kick = 0

    def __init__(self, bot, admin, mq):
        bot.load_commands_from(self)
        self.admin = admin
        self.mq = mq

    @botcmd
    @logerrors
    def deowl(self, message):
        '''Your friendly neigh-bourhood pest control. Has a cooldown'''
        speaker = message.sender_jid
        '''Only kicks :owl, long cooldown'''
        if self.last_owl_kick:
            if (datetime.now() - self.last_owl_kick).seconds < self.kick_owl_delay:
                self.log_deowl(speaker, False)
                return "I'm tired. Maybe another time?"
        log.debug("trying to kick owl ...")
        self.admin.kick_jid('owlowiscious@friendshipismagicsquad.com', ':sweetiestare:',
                        on_success=self.deowl_success_handler(speaker),
                        on_failure=self.deowl_failure_handler(speaker))
        return

    def deowl_success_handler(self, speaker):
        def handler():
            log.debug('deowl success')
            self.last_owl_kick = datetime.now()
            self.kick_owl_delay = random.gauss(2*60*60, 20*60)
            self.log_deowl(speaker, True)
        return handler

    def deowl_failure_handler(self, speaker):
        def handler():
            log.debug('deowl failure')
            self.log_deowl(speaker, False)
        return handler

    @logerrors
    def log_deowl(self, speaker, success):
        speaker = JID(speaker)
        timestamp = datetime.utcnow()
        mq_message = {
            'deowl':True,
            'room':speaker.user,
            'server':speaker.domain,
            'speaker': speaker.resource,
            'timestamp': timestamp.isoformat(' '),
            'success': success,
            }

        self.mq.send(json.dumps(mq_message).encode('utf-8'))

    @botcmd(hidden=True)
    def deoctavia(self, message):
        self.detavi(message)

    @botcmd
    @logerrors
    def detavi(self, message):
        '''For when there's too much of a good thing'''
        speaker = message.sender_nick
        log.debug("trying to kick "+speaker)
        target = 'Octavia' if self.admin.message_is_from_mod(message) else speaker
        self.admin.kick(target, ':lyraahem:')
        return
