import logging
from sleekxmpp.xmlstream.jid import JID

log = logging.getLogger(__name__)

class RoomMemberList():
    def __init__(self, members):
        self.members = members

    def __repr__(self):
        return "RoomMemberList({})".format(repr(self.members))

    def get_member_from_nickname(self, nickname):
        result = next((x for x in self.members if x.nickname == nickname), None)
        if not result:
            log.warning("Couldn't find member entry for nickname %s", nickname)
        return result

class RoomMember():
    def __init__(self, nickname, jid, affiliation, role):
        self.nickname = nickname
        self.jid = jid
        self.affiliation = affiliation
        self.role = role

    def can_do_admin_things(self):
        if self.role == "moderator": return True
        return self.affiliation in ('admin', 'owner')

    def __repr__(self):
        return "RoomMember({},{},{},{})".format(self.nick, self.jid, self.affiliation, self.role)

