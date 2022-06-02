from slixmpp import JID


class Presence:
    def __init__(self, muc_jid, user_jid, presence_type, message):
        self.muc_jid = JID(muc_jid)
        self.user_jid = JID(user_jid)
        self.presence_type = presence_type
        self.message = message
