import redis
from pprint import pformat
import re

r = redis.Redis(decode_responses=True)
r.ping()

datetime_re = re.compile(r'\d\d\d\d-\d\d-\d\d \d\d:\d\d')

seen_keys = r.keys("seen:*")
seen_values = r.mget(seen_keys)
seen_pairs = zip((x[5:] for x in seen_keys), seen_values)
seen_pairs = [x for x in seen_pairs if datetime_re.match(x[1])]
seen = dict(seen_pairs)

spoke_keys = r.keys("spoke:*")
spoke_values = r.mget(spoke_keys)
spoke_pairs = zip((x[6:] for x in spoke_keys), spoke_values)
spoke_pairs = [x for x in spoke_pairs if datetime_re.match(x[1])]
spoke = dict(spoke_pairs)

seen_spoke = {k: (seen.get(k, 'NULL'), spoke.get(k, 'NULL')) for d in (seen, spoke) for k in d.keys()}

# print(pformat(seen_spoke))
print(f"seen: {len(seen)} spoke: {len(spoke)} combined: {len(seen_spoke)}")
# print(pformat([(k) for k in spoke if not k in seen]))
# print(pformat([(k) for k in seen if not k in spoke]))

jidfornick_keys = r.keys("jidfornick:*")
jidfornick_values = r.mget(jidfornick_keys)
jidfornick = dict(zip((x[11:] for x in jidfornick_keys), jidfornick_values))
print(f"jidfornick: {len(jidfornick)}")

tell_keys = r.keys("tell:*")
tell = [(k[5:],sender,message)  for k in tell_keys for (sender,message) in r.hgetall(k).items()]
#print(pformat(tell, width=160))
print(f"tell: {len(tell)}")

ping_keys = r.keys("ping:*")
ping = [ (jid, k[5:])  for k in ping_keys for jid in r.smembers(k) ]
#print(pformat(ping))
print(f"ping: {len(ping)}")