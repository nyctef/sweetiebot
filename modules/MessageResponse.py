from html import escape as html_escape
from typing import TypeAlias
from slixmpp import JID


def to_html(text: str) -> str:
    return html_escape(text).replace("\n", "<br />")


class MessageResponse:
    def __init__(
        self,
        input: "str | MessageResponse",
        default_destination: JID | str | None,
        html: str | None = None,
    ) -> None:
        self.plain: str
        self.html: str
        self.destination: JID | str | None

        if isinstance(input, MessageResponse):
            self.plain = input.plain
            self.html = html or input.html or to_html(input.plain)
            self.destination = input.destination or default_destination
        else:
            self.plain = input
            self.html = html or to_html(input)
            self.destination = default_destination


# the value returned from a bot command: None means that nothing should be sent back
CommandResult: TypeAlias = str | MessageResponse | None
