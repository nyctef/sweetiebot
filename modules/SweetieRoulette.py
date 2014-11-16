from utils import logerrors, botcmd
import random
import logging

log = logging.getLogger(__name__)

class SweetieRoulette(object):
    def __init__(self, bot, admin):
        bot.load_commands_from(self)
        self.admin = admin
        self._spin()

    def _spin(self):
        self.current_chamber = random.randint(0, 5)
        log.debug("chamber on "+str(self.current_chamber))

    @botcmd
    @logerrors
    def spin(self, message):
        """Spin the barrel (see also: roulette)"""
        self._spin()
        return '*WHIIIIiiiiirr...*'

    @botcmd
    @logerrors
    def roulette(self, message):
        """Six bullets, one chamber (see also: spin)"""
        speaker = message.sender_nick

        self.current_chamber += 1
        self.current_chamber = self.current_chamber % 6
        if self.current_chamber == 0:
            return self.admin.kick(speaker, '*BANG*')
            self._spin()
        else:
            return '*click*'


