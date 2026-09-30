import logging
from slixmpp import JID

log = logging.getLogger(__name__)


class RoomMemberList:
    def __init__(self, members: list["RoomMember"]) -> None:
        self.members = members

    def __repr__(self) -> str:
        return "RoomMemberList({})".format(repr(self.members))

    def get_member_from_nickname(self, nickname: str | None) -> "RoomMember | None":
        result = next((x for x in self.members if x.nickname == nickname), None)
        if not result:
            log.warning("Couldn't find member entry for nickname %s", nickname)
        return result

    def get_nick_list(self) -> list[str]:
        return [x.nickname for x in self.members]


class RoomMember:
    def __init__(self, nickname: str, jid: JID | str, affiliation: str, role: str) -> None:
        self.nickname = nickname
        self.jid = jid
        self.affiliation = affiliation
        self.role = role

    def can_do_admin_things(self) -> bool:
        if self.role == "moderator":
            return True
        return self.affiliation in ("admin", "owner")

    def __repr__(self) -> str:
        return "RoomMember({},{},{},{})".format(
            self.nickname, self.jid, self.affiliation, self.role
        )
