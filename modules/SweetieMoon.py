import logging
import json
import requests
from utils import logerrors, botcmd

log = logging.getLogger(__name__)

class SweetieMoon(object):
    def __init__(self, bot=None):
        if bot:
            bot.load_commands_from(self)

    def phase_description(self, phase):
        descriptions = {
                'new moon': "hiding. Spoopiness levels are at a minimum and most incantations are safe to perform. Spoopiness levels are at a minimum and most incantations are safe to perform.",
                'waxing crescent': "growing.",
                'first quarter': "half full. Preparations are not necessary yet.",
                'waxing gibbous': "almost full. It is still safe to go out after dark, but be careful.",
                'full moon': "full. If you have not yet made it to a shelter, please do so imminently",
                'waning gibbous': "waning, thankfully. Normalcy will resume shortly.",
                'last quarter': "half empty.",
                'waning crescent': "almost gone. Sun festival preparations will begin presently.",
                }
        return descriptions.get(phase.lower(), 'unknown. This is worrying.')

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

        description = self.phase_description(phase)
        percentage = result.get('fracillum', None)
        if not percentage:
            percentage = phase_percentage(phase)

        return 'Currently, the moon is {} full and {}'.format(percentage, description)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    moon = SweetieMoon()
    print(moon.moon(None))
