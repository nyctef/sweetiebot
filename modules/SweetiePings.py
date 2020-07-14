from modules import MUCJabberBot
from utils import logerrors, botcmd
from datetime import datetime
from sleekxmpp.jid import JID

class PingStorageRedis(object):
    def __init__(self, store):
        self.store = store
    
    def get_ping_group_members(self, group):
        return [x.decode() for x in self.store.smembers(f'ping:{group}')]
    
    def add_ping_group_member(self, group, member):
        return self.store.sadd(f'ping:{group}', str(member))
    
    def remove_ping_group_member(self, group, member):
        return self.store.srem(f'ping:{group}', str(member))
    
    def get_ping_group_list(self):
        group_names = [x.decode() for x in self.store.keys('ping:*')]
        groups = [(x, self.store.scard(x)) for x in group_names]
        groups = [(x[len('ping:'):], count) for (x, count) in groups]
        return [(group, count) for (group, count) in groups if count > 0]
    
    def get_ping_groups_for_member(self, member):
        result = []
        for group in self.store.keys('ping:*'):
            group_members = self.store.smembers(group)
            group_usernames = list(map(lambda x: x.decode('utf-8'), group_members))
            if member in group_usernames:
                group_name = group[len('ping:'):].decode('utf-8')
                result.append(group_name)
        return result

class PingStoragePg(object):
    def __init__(self, conn):
        self.cur = conn.cursor()
    
    def get_ping_group_members(self, group):
        return []

class SweetiePings:
    def __init__(self, bot, store):
        bot.load_commands_from(self)
        self.bot = bot
        self.storage = PingStorageRedis(store)

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
        targets = self.storage.get_ping_group_members(group)
        if not len(targets):
            return "no users found in group '{}'".format(group)
        for target in targets:
            self.bot.send_chat_message(formatted_message)
        return "ping sent to {} users".format(len(targets))


    @botcmd
    @logerrors
    def subscribe(self, message):
        '''[group] Add yourself to a pingable group'''
        group = message.args
        if not group or group.isspace():
            return 'Usage: subscribe group_name'
        jid = message.user_jid
        if not jid:
            return "Sorry, I don't know what your JID is"
        added = self.storage.add_ping_group_member(group, str(jid))
        if added:
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
        if not jid:
            return "Sorry, I don't know what your JID is"
        removed = self.storage.remove_ping_group_member(group, str(jid))
        if removed:
            return "User {} removed from group '{}'".format(jid, group)
        else:
            return "User {} was not in group '{}'".format(jid, group)

    @botcmd
    @logerrors
    def groups(self, message):
        '''List available groups for pings'''
        result = []
        for (group, count) in self.storage.get_ping_group_list():
            result.append(f'{group} ({count})')

        return f'Available groups: {", ".join(result)}. See also !users and !mygroups'

    @botcmd
    @logerrors
    def users(self, message):
        '''[group] Lists users currently in a pingable group'''
        if not message.args:
            return 'Usage: users group_name'
        group = message.args
        targets = self.storage.get_ping_group_members(group)
        if not len(targets):
            return "no users found in group '{}'".format(group)
        usernames = map(lambda x: JID(x.decode('utf-8')).user, targets)
        return ('Users in {}: {}'.format(group, ', '.join(usernames)) +
            '. See also !groups and !mygroups')

    @botcmd
    @logerrors
    def mygroups(self, message):
        '''List pingable groups that you are currently subscribed to'''
        jid = message.user_jid
        if not jid:
            return "Sorry, I don't know what your JID is"
        result = self.storage.get_ping_groups_for_member(str(jid))

        if not len(result):
            return 'User {} is not currently subscribed to any pingable groups'.format(
                    jid)
        return ('Your groups: {}'.format(', '.join(result)) +
            '. See also !users and !groups')

    # aliases:
    @botcmd(hidden=True)
    def group(self, message): return self.users(message)

    @botcmd(hidden=True)
    def subs(self, message): return self.mygroups(message)

    @botcmd(hidden=True)
    def mysubs(self, message): return self.mygroups(message)

    @botcmd(hidden=True)
    def subscriptions(self, message): return self.mygroups(message)

    @botcmd(hidden=True)
    def unsub(self, message): return self.unsubscribe(message)

    @botcmd(hidden=True)
    def sub(self, message): return self.subscribe(message)

