# coding:utf8

# add parent dir to path since we're not using any fancy frameworks for
# these tests
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)

from sweetiebot import build_sweetiebot
import sleekxmpp
import queue
from utils import logerrors
from threading import Event

'''

needed: wrap around sweetiebot but don't call serve_forever; process pending messages instead
some way of logging and waiting for messages from a sleekxmpp bot to do tests with

'''

class LoggingXMPPClient():
    """ xmpp client that logs all received messages to a list on a bg thread"""
    def __init__(self):
        self.messages = []


class FakeXMPPUser():
    """ helper class for making assertions about the state of a chat"""
    def __init__(self, timeout, username, password, nick):
        print("creating bot..")
        self.nick = nick
        self.chatroom =  'sweetiebot_playground@conference.friendshipismagicsquad.com'
        bot = sleekxmpp.ClientXMPP(username, password)
        bot.add_event_handler('session_start', self.on_start)
        bot.add_event_handler('message', self.on_message_received)
        bot.register_plugin('xep_0045')
        self.muc = bot.plugin['xep_0045']
        self.bot = bot
        self.timeout = timeout
        self.messages = queue.Queue()
        self.has_joined_chat = Event()
        print('fake user connecting ..')
        if self.bot.connect():
            print('.. connected')
            self.bot.process()
        else:
            raise 'unable to connect'

    def on_start(self, event):
        print('fake user on_start')
        self.bot.get_roster()
        self.bot.send_presence()
        print('fake user joining {} as {}'.format(self.chatroom, self.nick))
        self.muc.joinMUC(self.chatroom, self.nick, wait=True)
        self.has_joined_chat.set()

    def send_message(self, message, html=None):
        self.bot.send_message(mto=self.chatroom, mbody=message, mhtml=html, mtype='groupchat')

    def has_received_message(self, message_re=None, sender=None):
        return self.messages.get(True, self.timeout)
        #if message_re is not None and not message_re.match(message.message_text):
            #print('failed at re')
            #continue
        #if sender is not None and sender != message.sender_nick:
            #print('failed {} != {}'.format(sender, message.sender_nick))
            #continue
        #found_message = message
        #if found_message is None:
            #raise Exception()
        #return found_message

    @logerrors
    def on_message_received(self, message):
        #print('message recieved: '+str(message))
        if message['subject'] or message['mucnick'] == 'admin':
            return
        self.messages.put(message)

    def check_for_messages(self):
        pass# self.bot.process()

    def quit(self):
        self.bot.disconnect()


chatroom = 'sweetiebot_playground@conference.friendshipismagicsquad.com'

def stay_awhile_and_listen():
    import time
    #TODO: replace any usage of this function with something that spins on a condition or actually waits for a specific message id
    time.sleep(1)

def bot_connects_to_chat():
    #username = 'sweetiebutt@friendshipismagicsquad.com/sweetiebutt'
    #password = open('password.txt', 'r').read().strip()
    import config
    config.fake_redis = True
    config.chatroom = config.test_chatroom
    sweet = build_sweetiebot()
    stay_awhile_and_listen()
    return sweet

def admin_connects_to_chat():
    import config
    print("connecting admin...")
    username = 'nyctef@friendshipismagicsquad.com/sweetieadmin'
    password = config.admin_password
    admin = FakeXMPPUser(10, username, password, 'admin')
    print("joining admin... ")
    assert admin.has_joined_chat.wait(10)
    return admin

def test_user_connects_to_chat():
    username = 'sweetietest@friendshipismagicsquad.com/asdftest'
    password = 'asdf'
    test_user = FakeXMPPUser(10, username, password, 'test_user')
    assert test_user.has_joined_chat.wait(10)
    return test_user

def when_bot_is_pinged(admin):
    admin.send_message('Sweetiebot: this is a ping')

def bot_responds_with_sass(admin):
    stay_awhile_and_listen()
    admin.check_for_messages()
    admin.has_received_message(sender='Sweetiebot')

def send_and_wait(message):
    global admin
    admin.send_message(message, message)
    admin.has_received_message()

def spam_bot_with_stuff(admin):
    send_and_wait('Sweetiebot: help')
    send_and_wait('Sweetiebot: confirmed c/d')
    send_and_wait('<a href="http://google.com/">google ?q=&#x192;</a>')
    send_and_wait('https://www.youtube.com/watch?v=-hZY8ibqKyA')
    send_and_wait('Sweetiebot: roll 1d20')
    send_and_wait('/me pets Sweetiebot')
    send_and_wait('Sweetiebot: spin')
    send_and_wait('Sweetiebot: seen')
    send_and_wait('Sweetiebot: seen test_user')
    send_and_wait('Sweetiebot: seen admin')

def test_admin(admin):
    send_and_wait('Sweetiebot: banlist')

def test_lookup(admin):
    send_and_wait('Sweetiebot: yt pfudor')
    send_and_wait('Sweetiebot: woon')
    send_and_wait('Sweetiebot: jita tayra')

def test_pings(admin):
    send_and_wait('Sweetiebot: subscribe')
    send_and_wait('Sweetiebot: subscribe test_ping')
    send_and_wait('Sweetiebot: subscribe   test_ping')
    send_and_wait('Sweetiebot: ping test_ping')
    send_and_wait('Sweetiebot: groups')
    send_and_wait('Sweetiebot: users test_ping')
    send_and_wait('Sweetiebot: ping test_ping this is a test ping message')
    send_and_wait('Sweetiebot: unsubscribe')
    send_and_wait('Sweetiebot: unsubscribe test_ping')
    send_and_wait('Sweetiebot: ping test_ping should not ping anyone')
    send_and_wait('Sweetiebot: groups')

def bot_tries_to_kick_admin():
    admin.send_message('Sweetiebot: kick admin')
    stay_awhile_and_listen()

def bot_kicks_test_user():
    admin.send_message('Sweetiebot: kick test_user')
    stay_awhile_and_listen()
    stay_awhile_and_listen()

def bot_kicks_missing_user():
    send_and_wait('Sweetiebot: kick nobody')

def bot_kicks_missing_jid():
    send_and_wait('Sweetiebot: kickjid nobody@friendshipismagicsquad.com')

def bot_kicks_test_user_by_jid():
    admin.send_message('Sweetiebot: kickjid sweetietest@friendshipismagicsquad.com')
    stay_awhile_and_listen()
    stay_awhile_and_listen()

def fake_user_disconnects(admin):
    print('trying to kill admin'+str(admin))
    if admin: admin.quit()

def bot_disconnects(bot):
    print('trying to kill bot'+str(bot))
    if bot: bot.bot.disconnect()

admin = None
sweetie = None
test_user = None

def run_tests():
    global sweetie
    sweetie = bot_connects_to_chat()
    global admin
    admin = admin_connects_to_chat()
    global test_user
    test_user = test_user_connects_to_chat()
    #user_connects_to_chat()

    #TODO: make an attribute that logs method names automatically when they are run
    print("initial processing done")
    print("pinging bot")
    when_bot_is_pinged(admin)
    print("bot pinged")
    print("bot processed")
    bot_responds_with_sass(admin)
    bot_kicks_missing_user()
    bot_kicks_test_user()
    test_user = test_user_connects_to_chat()
    bot_kicks_missing_jid()
    bot_kicks_test_user_by_jid()
    bot_tries_to_kick_admin()

    spam_bot_with_stuff(admin)
    test_pings(admin)
    test_lookup(admin)
    test_admin(admin)

if __name__ == '__main__':
    try:
        import os,threading,time,faulthandler,traceback
        import logging
        #logging.getLogger().setLevel(logging.DEBUG)
        #logging.getLogger('modules.Message').setLevel(logging.DEBUG)
        #logging.getLogger('modules.MUCJabberBot').setLevel(logging.DEBUG)
        logging.getLogger('sleekxmpp').setLevel(logging.DEBUG)
        logging.getLogger('sleekxmpp.xmlstream.xmlstream').setLevel(logging.FATAL)
        #logging.getLogger('modules.SweetieAdmin').setLevel(logging.DEBUG)
        #logging.getLogger('modules.SweetieLookup').setLevel(logging.DEBUG)
        logging.getLogger('modules.SweetieSeen').setLevel(logging.DEBUG)

        run_tests()
    except:
        traceback.print_exc()
    finally:
        traceback.print_stack()
        fake_user_disconnects(admin)
        fake_user_disconnects(test_user)
        bot_disconnects(sweetie)
        if threading.active_count() != 1:
            print('waiting for all threads to end')
            time.sleep(5)
            print('threads remaining: {}'.format(threading.active_count()))
            faulthandler.dump_traceback()
        os._exit(1)
