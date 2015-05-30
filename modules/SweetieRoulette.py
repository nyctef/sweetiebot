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
        if message.is_pm:
            return ':lyraahem: no tampering with the gun under the table now'
        self._spin()
        return '*WHIIIIiiiiirr...*'

    @botcmd
    @logerrors
    def roulette(self, message):
        """Six bullets, one chamber (see also: spin)"""
        if message.is_pm:
            return ':lyraahem: suicide should be a social activity'
        speaker = message.sender_nick

        self.current_chamber += 1
        self.current_chamber = self.current_chamber % 6
        if self.current_chamber == 0:
            self._spin()
            if speaker:
                return self.admin.kick(speaker, '*BANG*')
            return 'BANG! You\'re dead.'
        else:
            return '*click*'


