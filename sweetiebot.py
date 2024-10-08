#!/usr/bin/env python
# coding: utf-8

import redis
import sys
import logging
from utils import randomstr
from modules import (
    MUCJabberBot,
    SweetieAdmin,
    SweetieChat,
    SweetieLookup,
    FakeRedis,
    SweetieRoulette,
    SweetieDe,
    SweetiePings,
    PingStorageRedis,
    PingStoragePg,
    PgWrapper,
    SweetieSeen,
    SeenStoragePg,
    SeenStorageRedis,
    SweetieTell,
    TellStorageRedis,
    TellStoragePg,
    SweetieDictionary,
    SweetieMoon,
    TableList,
    RandomizedList,
    make_experiment_object,
)
import time
import traceback


log = logging.getLogger(__name__)


class Sweetiebot(object):
    def __init__(
        self,
        nickname,
        bot,
        lookup,
        admin,
        chat,
        roulette,
        sweetiede,
        pings,
        moon,
    ):
        self.nickname = nickname
        self.bot = bot
        log.debug("setting unknown_command_callback on " + str(self.bot))
        self.bot.unknown_command_callback = self.unknown_command
        self.lookup = lookup
        self.admin = admin
        self.chat = chat
        self.roulette = roulette
        self.sweetiede = SweetieDe
        self.pings = pings
        self.moon = moon

    def unknown_command(self, message):
        log.debug("Sweetiebot unknown_command")
        return self.chat.random_chat(message)

    def process(self):
        self.bot.process()


def build_sweetiebot(config=None):
    if config is None:
        import config
    resource = config.nickname + randomstr()

    if config.pg_conn_str:
        dbwrapper = PgWrapper(config.pg_conn_str)
    else:
        raise Exception("pg connection string must be set")

    jid = config.username + "/" + resource
    nick = config.nickname
    room = config.chatroom
    password = config.password
    if config.hostname is not None:
        address = (config.hostname, config.port)
    else:
        address = ()

    bot = MUCJabberBot(jid, password, room, nick, address)

    lookup = SweetieLookup(bot)

    admin = SweetieAdmin(bot, config.chatroom)
    deowl_fails = RandomizedList(TableList(dbwrapper, "deowl_fails"))
    de = SweetieDe(bot, admin, deowl_fails)

    actions = RandomizedList(TableList(dbwrapper, "actions"))
    sass = RandomizedList(TableList(dbwrapper, "sass"))
    cadmusic = RandomizedList(TableList(dbwrapper, "cadmusic"))

    tell_storage = TellStoragePg(dbwrapper)
    tell = SweetieTell(bot, tell_storage)

    dictionary = SweetieDictionary(bot)
    chat = SweetieChat(bot, actions, sass, config.chatroom, cadmusic, tell, dictionary)

    roulette = SweetieRoulette(bot, admin)
    ping_storage = PingStoragePg(dbwrapper)
    pings = SweetiePings(bot, ping_storage)
    moon = SweetieMoon(bot)

    seen_storage = SeenStoragePg(dbwrapper)
    seen = SweetieSeen(bot, seen_storage)

    sweet = Sweetiebot(
        config.nickname, bot, lookup, admin, chat, roulette, de, pings, moon
    )
    return sweet


def setup_logging(config):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers = []

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p"
    )
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.DEBUG if config.debug else logging.INFO)
    streamhandler.setFormatter(formatter)
    root_logger.addHandler(streamhandler)

    try:
        if config.app_insights_key is not None:
            from opencensus.ext.azure.log_exporter import AzureLogHandler

            azure_handler = AzureLogHandler(instrumentation_key=config.app_insights_key)
            azure_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(azure_handler)
    except Exception:
        logging.exception("Failed to set up azure logging")

    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(
        logging.WARNING
    )
    logging.getLogger("slixmpp.plugins.xep_0199.ping").setLevel(logging.WARNING)
    logging.getLogger("slixmpp.xmlstream.xmlstream").setLevel(logging.WARNING)
    logging.getLogger("opencensus.ext.azure.common.transport").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


if __name__ == "__main__":
    import config

    setup_logging(config)

    config.fake_redis = "--test" in sys.argv

    try:
        sweet = build_sweetiebot(config)
        log.info("sb process")
        sweet.process()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
