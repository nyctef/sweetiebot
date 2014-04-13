# add parent dir to path since we're not using any fancy frameworks for
# these tests
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)

from sweetiebot import build_sweetiebot
from MUCJabberBot import MUCJabberBot

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
                only_direct=False, command_prefix='###')
        self.bot.connect()
        self.timeout = timeout
    def send_message(self, message):
        self.bot.send(self.chatroom, message, message_type='groupchat')
    def has_received_message(self, message_re=None, sender=None):
        raise Exception()
    def join_room(self, chatroom, nick):
        self.bot.join_room(chatroom, nick)
        self.chatroom = chatroom
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
    sweet, _ = build_sweetiebot()
    sweet.join_room(chatroom, nickname)
    stay_awhile_and_listen()
    return sweet

def admin_connects_to_chat():
    print("connecting admin...")
    nickname = 'admin'
    username = 'nyctef@friendshipismagicsquad.com/sweetieadmin'
    password = open('nycpassword.txt', 'r').read().strip()
    admin = FakeXMPPUser(1000, username, password)
    print("joining admin... ")
    admin.join_room(chatroom, nickname)
    # todo: block on chatroom join
    stay_awhile_and_listen()
    return admin


def when_bot_is_pinged(admin):
    admin.send_message('Sweetiebot: this is a ping')

def bot_responds_with_sass(admin):
    admin.check_for_messages()
    admin.has_received_message(sender='Sweetiebot')

def admin_disconnects(admin):
    admin.quit()

def bot_disconnects(bot):
    bot.bot.quit()

def run_tests():
    sweetie = bot_connects_to_chat()
    admin = admin_connects_to_chat()
    #user_connects_to_chat()

    sweetie.bot.conn.Process(100)
    #TODO: make an attribute that logs method names automatically when they are run
    print("initial processing done")
    print("pinging bot")
    when_bot_is_pinged(admin)
    stay_awhile_and_listen()
    print("bot pinged")
    sweetie.bot.conn.Process(100)
    print("bot processed")
    bot_responds_with_sass(admin)

    admin_disconnects(admin)
    bot_disconnects(sweetie)



if __name__ == '__main__':
    run_tests()
