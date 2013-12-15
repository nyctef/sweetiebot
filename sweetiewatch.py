from jabberbot import JabberBot
from datetime import datetime
from azure.servicebus import *
import json
import random
import xmpp

class SweetieWatch(JabberBot):

    def randomstr(self):
        return ('%08x' % random.randrange(16**8))

    def __init__(self, nickname, account_key, issuer, \
            *args, **kwargs):
        resource = 'sweetiewatch' + self.randomstr()

        self.bus_service = ServiceBusService(service_namespace='jabber-fimsquad',\
                account_key=account_key, issuer=issuer)
        self.topic = 'chat-general'

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
        msg = Message(jsonstr)
        try:
            self.bus_service.send_topic_message(self.topic, msg)
        except Exception as e:
            print("MESSAGE DELIVERY FAILED: "+str(e))


if __name__ == '__main__':
    account_key = open('sb_account_key.txt', 'r').read().strip()
    username = 'sweetiebutt@friendshipismagicsquad.com/sweetiebutt'
    password = open('password.txt', 'r').read().strip();
    issuer = 'owner'
    sweetiewatch = SweetieWatch('Sweetiebutt', account_key, issuer,\
            username, password)
    sweetiewatch.join_room('general@conference.friendshipismagicsquad.com', \
            'Sweetiebot')
    sweetiewatch.serve_forever()

