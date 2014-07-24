from MUCJabberBot import MUCJabberBot
from utils import logerrors
from jabberbot import botcmd
from datetime import datetime

class SweetiePings:
    def __init__(self, bot, store):
        bot.load_commands_from(self)
        self.bot = bot
        self.store = store

    def key(self, group):
        return 'ping:'+group

    @botcmd
    @logerrors
    def ping(self, message):
        group = message.args.split()[0]
        ping_message = message.args.split(None, 1)[1]
        sender = message.sender_nick
        time = datetime.now()
        formatted_message = '''{}

## sent by {} to {} at {} ##'''.format(ping_message, sender, group, time)
        targets = self.store.smembers(self.key(group))
        if not len(targets):
            return "no users found in group '{}'".format(group)
        for target in targets:
            self.bot.send_pm_to_jid(target, formatted_message)
        return "ping sent to {} users".format(len(targets))

    @botcmd
    @logerrors
    def subscribe(self, message):
        group = message.args
        jid = message.sender_jid
        num_added = self.store.sadd(self.key(group), str(jid))
        print('num_added: {}'.format(num_added))
        if num_added:
            return "User {} added to group '{}'".format(jid, group)
        else:
            return "User {} was already in group '{}'".format(jid, group)

    @botcmd
    @logerrors
    def unsubscribe(self, message):
        group = message.args
        jid = message.sender_jid
        num_removed = self.store.srem(self.key(group), str(jid))
        if num_removed:
            return "User {} removed from group '{}'".format(jid, group)
        else:
            return "User {} was not in group '{}'".format(jid, group)


