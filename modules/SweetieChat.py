import logging
import re
import random
import hashlib
from random import randint
from utils import logerrors, botcmd
from modules.MessageResponse import MessageResponse, CommandResult
from modules.MUCJabberBot import MUCJabberBot
from modules.Message import Message
from modules.SweetieDictionary import SweetieDictionary
from modules.SweetieTell import SweetieTell
from modules.TableList import RandomizedList
from urllib.parse import urlparse

log = logging.getLogger(__name__)


class SweetieChat(object):
    urlregex = re.compile(
        r"((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@"
        + r")?[A-Za-z0-9.-]+|(?:www.|[-;:&=\+\$,\w]+@)[A-Za"
        + r"-z0-9.-]+)((?:\/[\+~%\/.\w_-]*)?\??(?:[-\+=&:\/"
        + r";%@.\w_]*)#?(?:[\w]*))?)"
    )

    emotes = [
        ":sweetie:",
        ":sweetiecrack:",
        ":sweetiederp:",
        ":sweetiedust:",
        ":sweetieglee:",
        ":sweetieidea:",
        ":sweetiemad:",
        ":sweetiepleased:",
        ":sweetieoops:",
        ":sweetieread:",
        ":sweetiescheme:",
        ":sweetieshake:",
        ":sweetieshrug:",
        ":sweetiesmug:",
        ":sweetiestare:",
        ":sweetietwitch:",
        ":egstare:",
        ":sweetiesiren:",
        ":sweetieskeptical:",
        ":sweetiedesk:",
        ":sweetiesalute:",
        ":sweetieawesome:",
        ":sweetiecreep:",
        ":sweetieeyes:",
        ":sweetiefsjal:",
        ":sweetielod:",
        ":sweetienom:",
        ":sweetieohyou:",
        ":sweetiesmeel:",
        ":gsweetieread:",
    ]

    lunabeh_top = 10
    lunabeh_count = 0
    target = "<target>"
    chattiness = 0.02

    def __init__(
        self,
        bot: MUCJabberBot,
        actions: RandomizedList,
        sass: RandomizedList,
        chatroom: str,
        cadmusic: RandomizedList,
        tell: SweetieTell,
        dictionary: SweetieDictionary,
    ) -> None:
        self.bot = bot
        self.bot.load_commands_from(self)
        self.nickname = self.bot.nick
        self.actions = actions
        # shadows the `sass` command method, which has already been registered above
        self.sass = sass  # type: ignore[method-assign, assignment]
        self.chatroom = chatroom
        self.cadance_musics_log = cadmusic
        self.tell = tell
        self.dictionary = dictionary

    def cuddle(self, message: Message) -> str:
        log.debug("cuddle")
        if "pets" in message.message_text:
            return "/me purrs " + random.choice(self.emotes)
        action = self.actions.get_next()
        action = action.replace("<target>", message.sender_nick)  # type: ignore[arg-type]
        return action + " " + random.choice(self.emotes)

    @logerrors
    def get_page_titles(self, message: str) -> str | None:
        matches = self.urlregex.findall(message)
        matches = [x[0] for x in matches]
        matches = list(map(self.youtube_filter, matches))
        matches = list(map(self.twitter_filter, matches))
        matches = list(map(self.imgur_filter, matches))
        matches = list(map(self.deviantart_filter, matches))
        results = list(map(self.get_page_title, matches))
        results = [result for result in results if result is not None]
        results = list(filter(self.title_filter, results))
        results = list(map(self.remove_extra_whitespace, results))
        if not len(results):
            return None
        return " / ".join(results)

    def get_page_title(self, url: str) -> str | None:
        if "oembed" in url:
            return self.get_oembed_page_title(url)

        from bs4 import BeautifulSoup
        import requests

        try:
            # sadly some sites (ie twitter.com) block "unsupported" browsers, so we have to lie about our user-agent
            headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
            }
            res = requests.get(url, timeout=5, headers=headers)
            if res.status_code != 200:
                log.warning("error fetching url " + url + " : " + str(res.status_code))
                return None
            # don't try and download big things
            content = res.raw.read(100000 + 1, decode_content=True)
            if len(content) > 100000:
                log.warning("skipping download of {} due to content length > 100000")
                return  # type: ignore[return-value]
            if "html" not in res.headers["content-type"]:
                log.warning("didn't get html from request, skipping")
                return  # type: ignore[return-value]
            soup = BeautifulSoup(res.text, "html.parser")
            return soup.title.string  # type: ignore[union-attr]
        except Exception as e:
            log.warning("error fetching url " + url + " : " + str(e))

    def get_oembed_page_title(self, url: str) -> str | None:
        import json
        import requests

        try:
            headers = {"user-agent": "sweetiebot"}
            res = requests.get(url, timeout=5, headers=headers)
            result = json.loads(res.text)
            if "title" in result and "author_name" in result:
                return result["title"] + " by " + result["author_name"]
            elif "html" in result:
                # because twitter's oembed api isn't as helpful
                from bs4 import BeautifulSoup
                return BeautifulSoup(result["html"], "html.parser").get_text(" ")
            else:
                raise Exception("Couldn't find appropriate oembed properties in "+url)
        except Exception as e:
            log.warning("error fetching url " + url + " : " + str(e))

    def title_filter(self, result: str) -> bool:
        if result.strip() == "imgur: the simple image sharer":
            return False
        if result.strip() == "Imgur":
            return False
        if result.strip() == "Imgur: The most awesome images on the Internet":
            return False
        if result.strip() == "Imgur: The magic of the Internet":
            return False
        if "jiffier gifs through HTML5 Video Conversion" in result.strip():
            return False
        return True

    def remove_extra_whitespace(self, result: str) -> str:
        result = result.replace("\n", "")
        result = result.replace("\r", "")
        result = re.sub(r"\s+", " ", result)
        return result

    def youtube_filter(self, link: str) -> str:
        parsed = urlparse(link)
        if "youtube" in parsed.netloc.replace(".", ""):
            return "https://www.youtube.com/oembed?format=json&url=" + link
        return link

    def twitter_filter(self, link: str) -> str:
        parsed = urlparse(link)
        if "twitter" in parsed.netloc:
            return "https://publish.twitter.com/oembed?format=json&url=" + link
        return link

    def imgur_filter(self, link: str) -> str:
        imgurregex = re.compile(r"^http(s)?://i.imgur.com/([a-zA-Z0-9]*)\..*$")
        match = imgurregex.match(link)
        if match:
            replacement = "http://imgur.com/" + match.group(2)
            log.debug("replacing " + link + " with " + replacement)
            return replacement
        return link

    def deviantart_filter(self, link: str) -> str:
        devartregex = re.compile(r"^http(s)?://\w+\.deviantart\.[\w/]+-(\w+)\.\w+$")
        match = devartregex.match(link)
        if match:
            replacement = (
                "http://backend.deviantart.com/oembed?url=http://fav.me/"
                + match.group(2)
            )
            log.debug("replacing " + link + " with " + replacement)
            return replacement
        return link

    def get_youtube_links(self, text: str) -> list[str]:
        youtuberegex = re.compile(
            r"(?:https?://)?(?:www\.)?(?:youtube|youtu)\.(?:com|be)/(?:watch\?v=|embed/|v/|[^ ]+\?v=)?(?:[^&=%\?]{11})"
        )
        links = youtuberegex.findall(text)
        if links:
            log.debug("found youtube links: {}".format(links))
        return links

    def do_cadance_musics(self, mess: Message) -> None:
        if mess.user_jid == "princess_cadence@friendshipismagicsquad.com":
            for link in self.get_youtube_links(mess.message_text):
                self.cadance_musics_log.add_line(link)
                log.info("Added {} to cadmusic".format(link))

    @logerrors
    def random_chat(self, mess: Message) -> CommandResult:
        """Does things"""
        log.debug("SweetieChat random chat")
        message = mess.message_text
        is_ping = mess.is_ping

        # logs Cadance musics
        self.do_cadance_musics(mess)

        tells = self.tell.get_messages_for(mess)
        if tells:
            return tells

        titles = self.get_page_titles(message)
        if titles:
            return titles

        random_junk = self.get_random_junk(mess)
        if random_junk:
            return random_junk

        if is_ping:
            return self.sass.get_next()  # type: ignore[attr-defined]

    def get_random_junk(self, mess: Message) -> CommandResult:
        message = mess.message_text
        sender = mess.sender_nick

        # if ":lunaglee:" in message.lower():
        #    self.bot.kick(sender, 'Don\'t upset my big sister! :sweetiemad:')
        #    return

        if re.findall(r"\bc/d\b", message):
            return sender + ": " + random.choice(["c", "d"])  # type: ignore[operator]

        is_ping = mess.is_ping
        if "yiff" in message.lower() and is_ping:
            return sender + ": yiff in hell, furfag :sweetiemad:"  # type: ignore[operator]

        if ":lunabeh:" in message.lower() and (
            sender == ":owl" or "luna" in sender.lower()  # type: ignore[union-attr]
        ):
            self.lunabeh_count = self.lunabeh_count + 1

        if self.lunabeh_count > self.lunabeh_top:
            self.lunabeh_top = randint(7, 15)
            self.lunabeh_count = 1
            return ":lunabeh:"

        if message.startswith("/me ") and is_ping:
            return self.cuddle(mess)

        if mess.command and mess.command.lower() == "no":
            return mess.nickname + " yes! :sweetieglee:"

        if mess.command == "how":
            xisyre = r"(.+?)\s+(?:is|are|was|were)\s+(.+?)\s*(?:\?)?\s*$"
            match = re.match(xisyre, mess.args)  # type: ignore[arg-type]
            if match:
                x = match.group(1)
                y = match.group(2)
                percent = self.hashpercent(x + y)
                return "{}: {} [{}% {}]".format(sender, y, percent, x)
            if "do you do" in mess.args.lower():  # type: ignore[union-attr]
                return "How do you do?"

            return "to be honest, I'm not sure"

        if mess.command in ("will", "should", "do"):
            return self.eightball(mess)

        if mess.command == "what" and mess.args.lower().startswith("is love"):  # type: ignore[union-attr]
            link = "http://i.imgur.com/nhMLKUB.gif"
            text = "baby don't hurt me"
            return MessageResponse(
                "{} [ {} ]".format(text, link),
                None,
                html='<a href="{}">{}</a>'.format(link, text),
            )

        if mess.command == "what":
            whatisre = r"\s*(?:is|are)\s+(.+?)\s*(?:\?)?\s*$"
            match = re.match(whatisre, mess.args)  # type: ignore[arg-type]
            if match:
                term = match.group(1)
                return self.dictionary.get_definition(term)

        if re.match(r"^\s*hey\s+now\s*$", message, re.IGNORECASE):
            return "you're an all star"

        if re.match(r".+is gay\s*$", message, re.IGNORECASE) or re.match(
            r"^gay$", message, re.IGNORECASE
        ):
            return sender + ": mlyp"  # type: ignore[operator]

    def hashpercent(self, input: str) -> float:
        return int(hashlib.md5(input.encode()).hexdigest(), 16) % 10001 / 100

    @botcmd(name="8ball")
    def eightball(self, mess: Message) -> str:
        if not mess.args:
            return "You need to ask something"
        chance = self.hashpercent(mess.args)
        choices = [
            "Definitely maybe.",
            "Eh, maybe.",
            "Possibly?",
            "Heh ... no.",
            "I'd give it a shot",
            "Ask Luna",
            "Get someone else to help you with this one.",
            "Try again ... actually don't bother trying again. It's not going to happen.",
            "Someone might feel bad enough for you that things will work out in your favor.",
            "Hope may not be warranted at this point.",
            "Patience is only a virtue if you're not a fuckup.",
            "Sometimes your best just isn't good enough. You still have to try, though.",
            "Just because you're necessary doesn't mean you're important. I wouldn't worry about it."
            "We do not anticipate further good news.",
            "The outcome will likely be another failure. At least you're consistent.",
            "Whatever you do, you still won't be worth a Wikipedia entry.",
            "Video games are a poor substitute for life. You probably want to stick to playing video games.",
            "Ask yourself if 10-year-old you would be proud of you.",
            "Your pets will still only see you as a source of food.",
            "You'll be surprised at what you can fuck up next. Other people won't be as surprised.",
            "The outcome looks successful, but nothing meaningful will change",
            "You can always stop procrastinating tomorrow.",
            "Yeah ... I guess.",
            "Hehe, *neigh*borhood :sweetieread: Oh, did you have a question?",
            "You can keep adjusting, but it will not make you well-adjusted.",
        ]
        return choices[int(chance) % len(choices)]

    @botcmd
    def cadmusic(self, message: Message) -> str:
        """Cadance Simulator 2016"""
        return "{} {} :{}:".format(
            self.cadance_musics_log.get_next(),
            random.choice(["horse music", "music for horses"]),
            random.choice(["3", "cadancefilly", "cadancehappy"]),
        )

    @botcmd(hidden=True)
    def quiet(self, message: Message) -> str:
        """I will only respond to pings"""
        self.chattiness = 0
        sender = message.sender_nick
        if "rainbow" in sender.lower():  # type: ignore[union-attr]
            return ":rdderp: okay then"
        if "luna" in sender.lower():  # type: ignore[union-attr]
            return ":lunabeh: fine"
        if "shard" in sender.lower():  # type: ignore[union-attr]
            return "I'll be quiet if you make more emotes for me :sweetiedust:"
        if "sparkle" in sender.lower():  # type: ignore[union-attr]
            return "Yes, my princess :sweetiepleased:"
        if "spike" in sender.lower():  # type: ignore[union-attr]
            return "Oh my! A dragon! :sweetie: Of course I'll be quiet"
        return sender + ": Sorry! I'll be quiet"  # type: ignore[operator]

    @botcmd(name="chat", hidden=True)
    def unquiet(self, message: Message) -> str:
        """I will chat every once in a while"""
        self.chattiness = 0.025
        return message.sender_nick + ": Ok, I'll start chatting again"  # type: ignore[operator]

    @botcmd
    def sass(self, message: Message) -> str:
        """[message] Remembers some sass to say back next time it is mentioned"""
        if len(message.args) > 400:  # type: ignore[arg-type]
            return "Sass too long :sweetiedust"
        if not message.args.strip():  # type: ignore[union-attr]
            return "What do you want me to remember?"
        if ":owl:" in message.args or message.sender_nick == ":owl":  # type: ignore[operator]
            return "No owls allowed! :sweetiedust:"
        reply = message.sender_nick + ": I'll remember that!"  # type: ignore[operator]
        self.sass.add_line(message.args.replace("\n", " ").strip())  # type: ignore[attr-defined, union-attr]
        return reply

    @botcmd
    def choose(self, message: Message) -> str:
        """[choices] Choose one of a (comma-separated) list of options"""
        return random.choice(list(map(lambda e: e.strip(), message.args.split(","))))  # type: ignore[union-attr]

    @botcmd
    def version(self, message: Message) -> str:
        with open("version.txt", "r") as versiontxt:
            return " ".join(map(str.strip, versiontxt.readlines()))
