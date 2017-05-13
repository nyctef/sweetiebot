from modules import MUCJabberBot
from utils import logerrors, botcmd
from datetime import datetime
from sleekxmpp.jid import JID

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
        '''[group] [message] Ping users in a group'''
        split = message.args.split(None, 1)
        if len(split) != 2:
            return 'Usage: ping group_name message'
        group = split[0]
        ping_message = split[1]
        sender = message.sender_nick or JID(message.sender_jid).bare
        time = datetime.now()
        formatted_message = '''{}

## sent by {} to {} at {} ##'''.format(ping_message, sender, group, time)
        targets = self.store.smembers(self.key(group))
        if not len(targets):
            return "no users found in group '{}'".format(group)
        for target in targets:
            self.bot.send_chat_message(formatted_message, target.decode('utf-8'))
        return "ping sent to {} users".format(len(targets))

    @botcmd
    @logerrors
    def subscribe(self, message):
        '''[group] Add yourself to a pingable group'''
        group = message.args
        if not group or group.isspace():
            return 'Usage: subscribe group_name'
        jid = message.user_jid
        num_added = self.store.sadd(self.key(group), str(jid))
        if num_added:
            return "User {} added to group '{}'".format(jid, group)
        else:
            return "User {} was already in group '{}'".format(jid, group)

    @botcmd
    @logerrors
    def unsubscribe(self, message):
        '''[group] Remove yourself from a pingable group'''
        group = message.args
        if not group or group.isspace():
            return 'Usage: unsubscribe group_name'
        jid = message.user_jid
        num_removed = self.store.srem(self.key(group), str(jid))
        if num_removed:
            return "User {} removed from group '{}'".format(jid, group)
        else:
            return "User {} was not in group '{}'".format(jid, group)

    @botcmd
    @logerrors
    def groups(self, message):
        '''List available groups for pings'''
        result = []
        for group in self.store.keys('ping:*'):
            num_in_group = self.store.scard(group)
            if num_in_group:
                group_name = group[len('ping:'):].decode('utf-8')
                result.append(group_name + ' ({})'.format(num_in_group))
        return 'Available groups: {}'.format(', '.join(result))

    @botcmd
    @logerrors
    def users(self, message):
        '''[group] Lists users currently in a pingable group'''
        if not message.args:
            return 'Usage: users group_name'
        group = message.args
        targets = self.store.smembers(self.key(group))
        if not len(targets):
            return "no users found in group '{}'".format(group)
        usernames = map(lambda x: JID(x.decode('utf-8')).user, targets)
        return 'Users in {}: {}'.format(group, ', '.join(usernames))
