from datetime import datetime
from modules import SweetieMQ
import json
import random
import logging
from time import sleep
from sleekxmpp.clientxmpp import ClientXMPP
from sleekxmpp.jid import JID
import traceback
import sys

class RestartException(Exception):
    pass

log = logging.getLogger(__name__)

class SweetieWatch():

    PING_FREQUENCY = 60

    def randomstr(self):
        return ('%08x' % random.randrange(16**8))

    def __init__(self, jid, password, room, nick, mq):
        self.nick = nick
        self.room = room
        self.jid = JID(jid)

        bot = ClientXMPP(jid, password)

        # disable ipv6 for now since we're getting errors using it
        bot.use_ipv6 = False

        bot.add_event_handler('session_start', self.on_start)
        bot.add_event_handler('message', self.on_message)

        bot.register_plugin('xep_0045')
        self._muc = bot.plugin['xep_0045']
        bot.register_plugin('xep_0199')
        bot.plugin['xep_0199'].enable_keepalive(30, 30)
        resource = 'sweetiewatch' + self.randomstr()

        self.mq = mq

        if not bot.connect(): raise 'could not connect'
        bot.process()

        self._bot = bot

    def on_start(self, event):
        print('sb on_start')
        self._bot.get_roster()
        self._bot.send_presence(ppriority=0)
        print('sb join {} as {}'.format(self.room, self.nick))
        self._muc.joinMUC(self.room, self.nick, wait=True)

    def on_message(self, message_stanza):
        type = message_stanza['type']
        if (type not in ['groupchat', 'chat']):
            return


        message = message_stanza['body']
        speaker = message_stanza['from']
        timestamp = datetime.utcnow()
        jsonstr = json.dumps({
            'message': message,
            'room': speaker.node,
            'server': speaker.domain,
            'speaker': speaker.resource,
            'timestamp': timestamp.isoformat(' ')
            })
        print('sending '+str(jsonstr))
        self.mq.send(jsonstr.encode('utf-8'))


if __name__ == '__main__':
    import config

    logging.getLogger().setLevel(logging.DEBUG)

    try:
        watch = SweetieWatch(config.username, config.password, config.chatroom,
                config.nickname, SweetieMQ(config))
        while True: sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
