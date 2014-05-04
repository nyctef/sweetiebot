from utils import logerrors
from jabberbot import botcmd
import random

class SweetieRoulette(object):
    def __init__(self, bot, admin):
        bot.load_commands_from(self)
        self.admin = admin
        self._spin()

    def _spin(self):
        self.current_chamber = random.randint(0, 5)
        print("chamber on "+str(self.current_chamber))

    @botcmd
    @logerrors
    def spin(self, mess, args):
        self._spin()
        return '*WHIIIIiiiiirr...*'

    @botcmd
    @logerrors
    def roulette(self, mess, args):
        speaker = mess.getFrom().getResource()

        self.current_chamber += 1
        self.current_chamber = self.current_chamber % 6
        if self.current_chamber == 0:
            self.admin.kick(speaker, '*BANG*')
            self._spin()
        else:
            return '*click*'


