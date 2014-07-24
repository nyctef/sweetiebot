# coding:utf8

# add parent dir to path since we're not using any fancy frameworks for
# these tests
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)

from sweetiebot import build_sweetiebot
from modules import MUCJabberBot

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
    def __init__(self, timeout, username, password):
        print("creating bot..")
        self.bot = MUCJabberBot('a_random_nick', username, password,
                command_prefix='###')
        self.bot.connect()
        self.bot.unknown_command_callback = self.message_received
        self.timeout = timeout
        self.messages = []
    def send_message(self, message):
        self.bot.send(self.chatroom, message, message_type='groupchat')
    def has_received_message(self, message_re=None, sender=None):
        found_message = None
        for message in self.messages:
            print('checking message '+message.message_text)
            if message_re is not None and not message_re.match(message.message_text):
                print('failed at re')
                continue
            if sender is not None and sender != message.sender_nick:
                print('failed {} != {}'.format(sender, message.sender_nick))
                continue
            found_message = message
        if found_message is None:
            raise Exception()
        return found_message
    def join_room(self, chatroom, nick):
        self.bot.join_room(chatroom, nick)
        self.chatroom = chatroom
    def message_received(self, message):
        print('message recieved: '+message.message_text)
        self.messages.append(message)
    def check_for_messages(self):
        self.bot.conn.Process(self.timeout)
    def quit(self):
        self.bot.quit()



chatroom = 'sweetiebot_playground@conference.friendshipismagicsquad.com'

def stay_awhile_and_listen():
    import time
    #TODO: replace any usage of this function with something that spins on a condition or actually waits for a specific message id
    time.sleep(1)

def bot_connects_to_chat():
    nickname = 'Sweetiebot'
    #username = 'sweetiebutt@friendshipismagicsquad.com/sweetiebutt'
    #password = open('password.txt', 'r').read().strip()
    import config
    config.fake_redis = True
    config.chatroom = config.test_chatroom
    sweet = build_sweetiebot()
    sweet.join_room(chatroom, nickname)
    stay_awhile_and_listen()
    return sweet

def admin_connects_to_chat():
    import config
    print("connecting admin...")
    nickname = 'admin'
    username = 'nyctef@friendshipismagicsquad.com/sweetieadmin'
    password = config.admin_password
    admin = FakeXMPPUser(1, username, password)
    print("joining admin... ")
    admin.join_room(chatroom, nickname)
    # todo: block on chatroom join
    stay_awhile_and_listen()
    return admin

def bot_processes_messages(sweetie):
    print('processes_messages')
    last_result = None
    while True:
        result = sweetie.bot.conn.Process(1)
        print(result)
        #god damn this api is terrible
        if result == '0' and last_result == '0': break
        last_result = result

def when_bot_is_pinged(admin):
    admin.send_message('Sweetiebot: this is a ping')

def bot_responds_with_sass(admin):
    stay_awhile_and_listen()
    admin.check_for_messages()
    admin.has_received_message(sender='Sweetiebot')

def spam_bot_with_stuff(admin):
    admin.send_message('Sweetiebot: confirmed c/d')
    admin.send_message('https://www.google.com/?q=ƒ')
    admin.send_message('<a href="http://google.com/">google</a>')
    admin.send_message('Sweetiebot: roll 1d20')
    admin.send_message('/me pets Sweetiebot')
    admin.send_message('Sweetiebot: jita plex')
    admin.send_message('Sweetiebot: woon')
    admin.send_message('Sweetiebot: spin')
    admin.send_message('Sweetiebot: subscribe test_ping')
    admin.send_message('Sweetiebot: ping test_ping this is a test ping message')
    admin.send_message('Sweetiebot: unsubscribe test_ping')
    admin.send_message('Sweetiebot: ping test_ping should not ping anyone')

def admin_disconnects(admin):
    admin.quit()

def bot_disconnects(bot):
    bot.bot.quit()

def run_tests():
    sweetie = bot_connects_to_chat()
    admin = admin_connects_to_chat()
    #user_connects_to_chat()

    bot_processes_messages(sweetie)
    #TODO: make an attribute that logs method names automatically when they are run
    print("initial processing done")
    print("pinging bot")
    when_bot_is_pinged(admin)
    stay_awhile_and_listen()
    print("bot pinged")
    bot_processes_messages(sweetie)
    print("bot processed")
    bot_responds_with_sass(admin)
    spam_bot_with_stuff(admin)
    bot_processes_messages(sweetie)
    stay_awhile_and_listen()

    admin_disconnects(admin)
    bot_disconnects(sweetie)



if __name__ == '__main__':
    run_tests()
