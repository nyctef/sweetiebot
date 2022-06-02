from utils import logerrors
import logging
from inspect import getdoc

log = logging.getLogger(__name__)


class MessageProcessor:
    def __init__(self, unknown_command_callback):
        self.commands = {}
        self.unknown_command_callback = unknown_command_callback

    def add_command(self, command_name, command_callback):
        self.commands[command_name] = command_callback

    @logerrors
    def process_message(self, message):
        log.debug("processing message with command: " + str(message.command))
        if message.command is not None:
            command = message.command
            if command == "help":
                return self.help(message)
            if command in self.commands:
                log.debug("running command " + command)
                return self.commands[command](message)

        log.debug("no matches found...")
        if self.unknown_command_callback is not None:
            log.debug("... running unknown_command_callback")
            return self.unknown_command_callback(message)

    @logerrors
    def help(self, message):
        if not message.is_pm:
            return "Hi! I'm Sweetiebot. Use 'help' in a PM for more details"

        commands = self.commands.values()
        result = []
        prefix = """
"""
        postfix = """
---
see source code or report issues at https://github.com/nyctef/sweetiebot
"""
        for command in commands:
            if not hasattr(command, "_bot_command"):
                continue
            if getattr(command, "_bot_command_hidden", False):
                continue
            command_name = command._bot_command_name
            docs = (getdoc(command) or "\n").splitlines()[0]
            result.append(command_name + ": " + docs)
        return prefix + "\n".join(sorted(result)) + postfix
