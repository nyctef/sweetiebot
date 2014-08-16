from html import escape as html_escape

def to_html(text):
    return html_escape(text).replace('\n', '<br />')

class MessageResponse:
    def __init__(self, input, default_destination, html=None):

        if isinstance(input, MessageResponse):
            self.plain = input.plain
            self.html = html or input.html or to_html(input.plain)
            self.destination = input.destination or default_destination
        else:
            self.plain = input
            self.html = html or to_html(input)
            self.destination = default_destination
