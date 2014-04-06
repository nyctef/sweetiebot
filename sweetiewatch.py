from jabberbot import JabberBot
from datetime import datetime
from SweetieMQ import SweetieMQ
import json
import random
import xmpp

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


if __name__ == '__main__':
    username = 'sweetiebutt@friendshipismagicsquad.com/sweetiebutt'
    password = open('password.txt', 'r').read().strip();
    sweetiewatch = SweetieWatch('Sweetiebutt', SweetieMQ(),\
            username, password)
    sweetiewatch.join_room('general@conference.friendshipismagicsquad.com', \
            'Sweetiebot')
    sweetiewatch.serve_forever()

