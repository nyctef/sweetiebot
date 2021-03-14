import logging
import re
import random
import hashlib
import requests
from random import randint
from utils import logerrors, botcmd
from pprint import pprint
from modules.MessageResponse import MessageResponse

log = logging.getLogger(__name__)


class SweetieDictionary(object):
    def __init__(self, bot):
        self.bot = bot
        self.bot.load_commands_from(self)

    @botcmd
    def define(self, message):
        """[terms] Word-explainer-tron 3000"""
        return self.get_definition(message.args)

    @logerrors
    def get_definition(self, term):
        # strip off any extra qualifiers
        term = re.sub(r"^((a|an|definition|of|the)\s+)+", "", term)
        if not term:
            return "Define what?"
        # grab a definition from urbandictionary.com
        url = "http://api.urbandictionary.com/v0/define?term={}".format(term)
        definitions = requests.get(url).json()["list"]
        definition = next(iter(definitions), None)
        if not definition:
            return "No definitions found for '{}'".format(term)
        return definition["definition"]
