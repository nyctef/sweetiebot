CREATE TABLE IF NOT EXISTS deowl_fails(id serial PRIMARY KEY, text TEXT);
ALTER TABLE deowl_fails ADD UNIQUE (text);

CREATE TABLE IF NOT EXISTS actions(id serial PRIMARY KEY, text TEXT);
ALTER TABLE actions ADD UNIQUE (text);

CREATE TABLE IF NOT EXISTS cadmusic(id serial PRIMARY KEY, text TEXT);
ALTER TABLE cadmusic ADD UNIQUE (text);

CREATE TABLE IF NOT EXISTS sass(id serial PRIMARY KEY, text TEXT);
ALTER TABLE sass ADD UNIQUE (text);

CREATE TABLE tell_jid_to_nick_mapping(nick TEXT PRIMARY KEY, jid TEXT);
CREATE TABLE tell_messages_by_sender(
    sender_jid TEXT,
    receiver_jid TEXT,
    messages TEXT[],
    PRIMARY KEY (sender_jid, receiver_jid)
);