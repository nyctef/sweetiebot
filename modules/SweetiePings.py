from MUCJabberBot import MUCJabberBot
from utils import logerrors
from jabberbot import botcmd
from datetime import datetime
from xmpp import JID

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
        split = message.args.split(None, 1)
        if len(split) != 2:
            return 'Usage: ping group_name message'
        group = split[0]
        ping_message = split[1]
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
        if not group or group.isspace():
            return 'Usage: subscribe group_name'
        jid = self.bot.get_jid_from_nick(message.sender_nick) \
            or message.sender_jid
        jid = JID(jid).getStripped()
        num_added = self.store.sadd(self.key(group), str(jid))
        if num_added:
            return "User {} added to group '{}'".format(jid, group)
        else:
            return "User {} was already in group '{}'".format(jid, group)

    @botcmd
    @logerrors
    def unsubscribe(self, message):
        group = message.args
        if not group or group.isspace():
            return 'Usage: unsubscribe group_name'
        jid = self.bot.get_jid_from_nick(message.sender_nick) \
            or message.sender_jid
        jid = JID(jid).getStripped()
        num_removed = self.store.srem(self.key(group), str(jid))
        if num_removed:
            return "User {} removed from group '{}'".format(jid, group)
        else:
            return "User {} was not in group '{}'".format(jid, group)

    @botcmd
    @logerrors
    def groups(self, message):
        result = []
        for group in self.store.keys('ping:*'):
            num_in_group = self.store.scard(group)
            if num_in_group:
                group_name = group[len('ping:'):]
                result.append(group_name + ' ({})'.format(num_in_group))
        return 'Available groups: {}'.format(', '.join(result))
