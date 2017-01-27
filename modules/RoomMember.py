import logging
from sleekxmpp.xmlstream.jid import JID

log = logging.getLogger(__name__)

class RoomMemberList():
    def __init__(self, members):
        self.members = members

    def __repr__(self):
        return "RoomMemberList({})".format(repr(self.members))

class RoomMember():
    def __init__(self, nick, jid, affiliation, role):
        self.nick = nick
        self.jid = jid
        self.affiliation = affiliation
        self.role = role

    def can_do_admin_things(self):
        if self.role == "moderator": return True
        return self.affiliation in ('admin', 'owner')

    def __repr__(self):
        return "RoomMember({},{},{},{})".format(self.nick, self.jid, self.affiliation, self.role)

