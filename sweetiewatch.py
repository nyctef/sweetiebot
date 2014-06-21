from jabberbot import JabberBot
from datetime import datetime
from modules import SweetieMQ
import json
import random
import xmpp
import logging
from time import sleep

class RestartException(Exception):
    pass

log = logging.getLogger(__name__)

class SweetieWatch(JabberBot):

    def randomstr(self):
        return ('%08x' % random.randrange(16**8))

    def __init__(self, nickname, mq, \
            *args, **kwargs):
        resource = 'sweetiewatch' + self.randomstr()

        self.mq = mq

        super(SweetieWatch, self).__init__(*args, res=resource, **kwargs)

    def callback_message(self, conn, mess):
        type = mess.getType()
        if (type not in ['groupchat', 'chat']):
            return

        props = mess.getProperties()
        # Ignore messages from before we joined
        if xmpp.NS_DELAY in props:
            return

        message = mess.getBody()
        speaker = mess.getFrom()
        timestamp = datetime.utcnow()
        jsonstr = json.dumps({
            'message': message,
            'room':speaker.getNode(),
            'server':speaker.getDomain(),
            'speaker': speaker.getResource(),
            'timestamp': timestamp.isoformat(' ')
            })
        print('sending '+jsonstr)
        self.mq.send(jsonstr)

    def on_ping_timeout(self):
        log.error('ping timeout')
        raise RestartException()


if __name__ == '__main__':
    import config
    while True: 
        try:
            sweetiewatch = SweetieWatch(config.nickname, SweetieMQ(config),\
                    config.username, config.password)
            connection = sweetiewatch.connect()
            if connection is None:
                print("failed to connect .. sleeping for 5 and continuing")
                sleep(5)
                continue
            sweetiewatch.join_room(config.chatroom, config.nickname)
            sweetiewatch.serve_forever()
        except RestartException:
            continue
        break

