import logging
import json
import requests
from utils import logerrors, botcmd

log = logging.getLogger(__name__)

class SweetieMoon(object):
    def __init__(self, bot=None):
        if bot:
            bot.load_commands_from(self)

    def phase_description(self, phase, percentage):
        descriptions = {
                'new moon': "It is the New Moon. Just like the old moon, but this one has Bluetooth.",
                'waxing crescent': "The moon is {percentage} full and waxing. Beware fleeting shadows in the corners of your vision",
                'first quarter': "The moon is half full, in the first quarter. You may hear a haunting wail outside tonight. Do not investigate.",
                'waxing gibbous': "The moon is {percentage} full and waxing. Test your doors and window locks now. Soon it will be too late ",
                'full moon': "The moon is full. Avoid windows. Do not look outside. Do not look into mirrors. It watches. It thirsts.",
                'waning gibbous': "The moon is {percentage} full and waning. Somehow you have survived. Next time you may not be so lucky.",
                'last quarter': "The moon is {percentage} full, in the third quarter. The woon can now be observed safely for short intervals with proper safety equipment.",
                'waning crescent': "The moon is {percentage} full and waning. Soon the moon shall hide, but do not lose vigilance.",
                }
        return descriptions.get(phase.lower(), 'The moon phase is unknown. This is worrying.').format(percentage=percentage)

    def phase_percentage(self, phase):
        descriptions = {
                'new moon': "0%",
                'first quarter': "50%",
                'full moon': "100%",
                'last quarter': "50%",
                }
        return descriptions.get(phase.lower(), 'partly')

    @botcmd
    def moon(self, message):
        coords = '51.4826N,0E'
        url = 'http://api.usno.navy.mil/rstt/oneday?date=today&time=now&coords={}'.format(coords)

        headers = { 'user-agent': 'sweetiebot' }
        res = requests.get(url, timeout=5, headers=headers)
        result = json.loads(res.text)

        log.debug(res.text)

        if result['error']:
            return 'moon is unhappy: '+result.type

        phase = result.get('curphase', None)
        if not phase:
            phase = result['closestphase']['phase']

        percentage = result.get('fracillum', None)
        if not percentage:
            percentage = self.phase_percentage(phase)

        return self.phase_description(phase, percentage)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    moon = SweetieMoon()
    print(moon.moon(None))
