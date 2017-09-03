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
                'new moon': "Currently, the moon is hiding. Spoopiness levels are at a minimum and most incantations are safe to perform.",
                'waxing crescent': "Currently, the moon is {percentage} full and growing.",
                'first quarter': "Currently, the moon is half full and growing. Preparations are not necessary yet, but be prepared.",
                'waxing gibbous': "Currently, the moon is {percentage} full and growing. It's almost full!",
                'full moon': "The moon is full and fully operational. Please be careful when leaving your designated shelter after dark.",
                'waning gibbous': "The moon is currently {percentage} full and waning.",
                'last quarter': "Currently the moon is {percentage} full and waning. Normalcy levels are now within acceptable tolerances.",
                'waning crescent': "The moon is {percentage} full and continuing to wane.",
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
