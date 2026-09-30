from utils import logerrors, botcmd
from datetime import datetime
import logging
import random
from typing import Callable
from modules.MUCJabberBot import MUCJabberBot
from modules.Message import Message
from modules.SweetieAdmin import SweetieAdmin
from modules.TableList import RandomizedList

log = logging.getLogger(__name__)


class SweetieDe(object):
    kick_owl_delay: float = 7200
    last_owl_kick: int | datetime = 0

    def __init__(
        self, bot: MUCJabberBot, admin: SweetieAdmin, failure_messages: RandomizedList
    ) -> None:
        bot.load_commands_from(self)
        self.admin = admin

        self.failures = failure_messages

    def chance(self, probability: float) -> bool:
        return random.random() < probability

    @botcmd
    @logerrors
    def deowl(self, message: Message) -> str:
        """Your friendly neigh-bourhood pest control. Has a cooldown"""
        if message.is_pm:
            return "But owl isn't here ... :sweetieskeptical:"

        if self.chance(0.7):
            return self.failures.get_next()
        return "I'm tired. Maybe another time?"

    def deowl_success_handler(self, speaker: str) -> Callable[[], None]:
        def handler() -> None:
            log.debug("deowl success")
            self.last_owl_kick = datetime.now()
            self.kick_owl_delay = random.gauss(2 * 60 * 60, 20 * 60)

        return handler

    def deowl_failure_handler(self, speaker: str) -> Callable[[], None]:
        def handler() -> None:
            log.debug("deowl failure")

        return handler

    @botcmd(hidden=True)
    def deoctavia(self, message: Message) -> None:
        self.detavi(message)

    @botcmd
    @logerrors
    def detavi(self, message: Message) -> None:
        """For when there's too much of a good thing"""
        speaker = message.sender_nick
        log.debug("trying to kick " + speaker)  # type: ignore[operator]
        target = "Octavia" if message.sender_can_do_admin_things() else speaker
        self.admin.kick(target, ":lyraahem:")  # type: ignore[arg-type]
        return
