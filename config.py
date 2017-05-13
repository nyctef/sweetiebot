from os import getenv
# Account and jabber server to connect to
username = getenv('SB_JID', 'bot_user@jabberserver')
# The chatroom to join
chatroom = getenv('SB_CHATROOM', 'test_room@conference.jabberserver')
# Account password
password = getenv('SB_PASSWORD', 'password1234')
# Nickname to use in chatroom
nickname = getenv('SB_NICKNAME', 'Sweetiebot')
# Optional: hostname to connect to (if different from the one specified in the JID)
hostname = getenv('SB_HOSTNAME', None)
# Optional: port to connect to (if different from 5222)
port = getenv('SB_PORT', 5222)
# Optional: turn on some debug features
debug = getenv('SB_DEBUG', False)

# Optional: An account key for Azure Service bus to chuck events at
sb_account_key = getenv('ASB_ACCOUNT_KEY', None)
# Optional: Issuer for service bus
sb_issuer = getenv('ASB_ISSUER', 'owner')
# Optional: Service namespace for azure service bus
sb_namespace = getenv('ASB_NAMESPACE', 'jabber-fimsquad')
# Optional: Service topic for azure service bus
sb_topic = getenv('ASB_TOPIC', 'chat-general-test')

# Optional: API key for pushbullet notifications
pushbullet_api = getenv('PB_API_KEY', None)
# Optional: Device ID for pushbullet notifications
pushbullet_device = getenv('PB_DEVICE_ID', None)

# Optional: Twitter API for putting twitter feeds into chat
twitter_key = getenv('TWITTER_API_KEY', None)
twitter_secret = getenv('TWITTER_API_SECRET', None)

# details for connecting to the EVE Online CREST api
crest_base_url = getenv('CREST_BASE', 'https://crest-tq.eveonline.com')
crest_client_id = getenv('CREST_ID', None);
crest_client_secret = getenv('CREST_CLIENT_SECRET', None)
crest_refresh_token = getenv('CREST_REFRESH_TOKEN', None)

# A url for the redis instance to connect to in the form redis://[:password]@host:port/dbnum
redis_url = getenv('REDIS_DB_URL', 'redis://sbredis:6379/0')
