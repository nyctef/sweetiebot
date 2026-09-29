from os import getenv

# Account and jabber server to connect to
username = getenv("SB_JID", "bot_user@jabberserver")
# The chatroom to join
chatroom = getenv("SB_CHATROOM", "test_room@conference.jabberserver")
# Account password
password = getenv("SB_PASSWORD", "password1234")
# Nickname to use in chatroom
nickname = getenv("SB_NICKNAME", "Sweetiebot")
# Optional: hostname and port to connect to (if different from the one specified in the JID)
hostname = getenv("SB_HOSTNAME", None)
port = getenv("SB_PORT", 5222)
# Optional: turn on some debug features
debug = getenv("SB_DEBUG", False)

# Connection string for backing storage
pg_conn_str = getenv("SB_PG_DB", None)

# Azure Monitor app insights key for opencensus logging
app_insights_key = getenv("SB_APPINSIGHTS_KEY", None)
