import logging
import json
import requests
from utils import logerrors, botcmd
from datetime import datetime
from astral import Astral

log = logging.getLogger(__name__)

class SweetieMoon(object):
    def __init__(self, bot=None):
        if bot:
            bot.load_commands_from(self)

    def phase_description(self, phase):
        case = int(phase*8)
        percentage = 1 - abs((2 * phase) - 1)
        descriptions = [
                "It is the New Moon. Just like the old moon, but this one has Bluetooth.",
                "The moon is {percentage} full and waxing. Beware fleeting shadows in the corners of your vision",
                "The moon is half full, in the first quarter. You may hear a haunting wail outside tonight. Do not investigate.",
                "The moon is {percentage} full and waxing. Test your doors and window locks now. Soon it will be too late ",
                "The moon is full. Avoid windows. Do not look outside. Do not look into mirrors. It watches. It thirsts.",
                "The moon is {percentage} full and waning. Somehow you have survived. Next time you may not be so lucky.",
                "The moon is {percentage} full, in the third quarter. The woon can now be observed safely for short intervals with proper safety equipment.",
                "The moon is {percentage} full and waning. Soon the moon shall hide, but do not lose vigilance.",
                ]
        return descriptions[case].format(percentage="{:.0f}%".format(percentage * 100))

    @botcmd
    def moon(self, message):
        try:
            phase = Astral().moon_phase(date=datetime.utcnow(), rtype=float) / 28
            return self.phase_description(phase)
        except Exception as e:
            return 'The moon phase is unknown. This is worrying. [{}]'.format(e)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    moon = SweetieMoon()
    print(moon.moon(None))
