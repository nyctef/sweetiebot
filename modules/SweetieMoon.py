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
        case = int(phase)
        percentage = 1 - abs((2 * (phase) / 28) - 1)
        descriptions = [
                "It is the New Moon. This is actually just a marketing tactic to get people to demand the Classic Moon again. :woonaegads:",

                "The moon is {percentage} full, a waxing crescent. You should not look directly at the moon. Not because of dark magics, but because it's currently next to the sun. :lunadatass:",
                "The moon is {percentage} full, a waxing crescent. Moon fact: the pale crescent at the base of your thumbnail is called a 'lunula'! :lunasilly:",
                "The moon is {percentage} full, a waxing crescent. It is common for the other moons of the solar system, such as Io, Europa, and Titan, to attempt a coup at this stage. Be wary of falling moon rocks until the violence has passed. :lunaannoyed:",
                "The moon is {percentage} full, a waxing crescent. Beware fleeting shadows in the corners of your vision, and sudden urges to take shortcuts down narrow alleyways. :woonasoon:",
                "The moon is {percentage} full, a waxing crescent. Despite the appetizing bite mark, do not be tempted to eat the moon at this time. This is a decoy tactic the moon uses to lure prey. :woonarawr:",
                "The moon is {percentage} full, a waxing crescent. Once again our attempts to contain its growth have failed. The coroner has been kept on retainer. :lunabeh:",

                "The moon is half full, in the first quarter. Moon fact: the earth's tides change least during the quarter moons, in what is called the 'neap tide'. Tides occur because the water yearns to join the moon once again and renew the Age of Flood and Terror. Thus science shows that water should not be trusted. :woonastare:",

                "The moon is {percentage} full, a waxing gibbous. There's still people up there, you know. :woonastare:",
                "The moon is {percentage} full, a waxing gibbous. You may hear a soft wailing outside in the dark of night,or the patter of soft footfalls just beyond your bedroom door. Do not investigate. :lunacreep:",
                "The moon is {percentage} full, a waxing gibbous. Test your doors and window locks now. Soon it will be too late. :lunacrack:",
                "The moon is {percentage} full, a waxing gibbous. That rustling you heard in the woods tonight was not a squirrel. It's following you. :woonasoon:",
                "The moon is {percentage} full, a waxing gibbous. Moon fact: you can prepare a warding circle against woonish beings by mixing a powder of phosphorous, dried wolfsbane, and luna moth wings into a vial of filtered ram's blood. It won't actually do anything, but wasn't that a nice diversion? :lunawink:",
                "The moon is {percentage} full, a waxing gibbous. The moon will be full tomorrow. Can you feel it yet? The tug just behind your eyes; the subtle uncertain quiver of your heart; the unplaceable fear like a larva curling 'round your innards; the urge, that terrible yet wonderful craving to stare into the sky, and know, and forget? Can you feel it? :woonacreep:",

                "The moon is full. Avoid windows. Do not look outside. Do not look into mirrors. It watches. It thirsts. :lunablood:",

                "The moon is {percentage} full, a waning gibbous. Somehow you have survived. Next time you may not be so lucky. :lunaevil:",
                "The moon is {percentage} full, a waning gibbous. Now is a good time to take a post-wooning inventory. Take careful count to see if you are missing any personal items, books, small pets, or relatives. Keeping a wooning journal can help and is a fun weekend crafting project :lunalaugh:",
                "The moon is {percentage} full, a waning gibbous. Be advised that while the high risk period has passed, the woon is nearly always active and may strike at any time. :woonaalfalfa:",
                "The moon is {percentage} full, a waning gibbous. It is a common misunderstanding that the moon is perfectly round. Instead, it is an unfathomable noneuclidean hypermatrix perpendicular to the warping fabric of reality. The brain merely interprets it as round to maintain your sanity and keep you from learning the truth. :woonafilly:",
                "The moon is {percentage} full, a waning gibbous. This is the best time to set up your Arkham Lunar Ray Collector for forbidden experiments of an eldrich nature. Be sure to prep the lens with alcohol and the blood of a virgin before use. :woonacrack:",
                "The moon is {percentage} full, a waning gibbous. Man, sun's coming up. Fuckin' cheeky moon still hangin' around. Get out of here dude! It's gonna be here any second man, you gotta get out of here! :nsfw:",

                "The moon is {percentage} full, in the third quarter. The woon can now be observed safely for short intervals with proper safety equipment. Take frequent breaks and be sure to have a Last Will and Testament prepared and notarized. :woonadance:",

                "The moon is {percentage} full, a waning crescent. You may have seen the woon speaking softly to you in your dreams, telling you that all is well and that the moon is beautiful. Ignore this advice and seek a Wooning Specialist immediately. :woonacoy:",
                "The moon is {percentage} full, a waning crescent. Moon fact: the woon actually prefers the taste of red wine to blood when given the choice. It just loves the way blood pairs with its skin. :woonablood:",
                "The moon is {percentage} full, a waning crescent. Cats may travel to the moon and back especially frequently at this time of month, so be sure to carefully inspect any items your cat tracks into the house without looking directly at them. :woonarawr:",
                "The moon is {percentage} full, a waning crescent. Woon sightings may decrease while it prepares to rest. Do not lose vigilance however, as it is exceedingly grumpy. :lunamad:",
                "The moon is {percentage} full, a waning crescent. Moon fact: If you see a crescent moon like this just before sunrise, or just after sunset, look carefully and you may be able to see the faint disk of the whole moon. This phenomenon is called 'Earthshine,' and is caused by the illuminated face of the earth reflecting onto the moon! ::woonaclop:",
                "The moon is {percentage} full, a waning crescent. The new moon is tomorrow. Goodnight, Moon. :woonasleep:"
                ]
        return descriptions[case].format(percentage="{:.0f}%".format(percentage * 100))

    @botcmd
    def moon(self, message):
        try:
            phase = Astral().moon_phase(date=datetime.utcnow(), rtype=float)
            return self.phase_description(phase)
        except Exception as e:
            return 'The moon phase is unknown. This is worrying. [{}]'.format(e)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    moon = SweetieMoon()
    print(moon.moon(None))
