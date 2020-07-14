CREATE TABLE IF NOT EXISTS deowl_fails(id serial PRIMARY KEY, text TEXT UNIQUE NOT NULL);

CREATE TABLE IF NOT EXISTS actions(id serial PRIMARY KEY, text TEXT UNIQUE NOT NULL);

CREATE TABLE IF NOT EXISTS cadmusic(id serial PRIMARY KEY, text TEXT UNIQUE NOT NULL);

CREATE TABLE IF NOT EXISTS sass(id serial PRIMARY KEY, text TEXT UNIQUE NOT NULL);

CREATE TABLE tell_jid_to_nick_mapping(nick TEXT PRIMARY KEY, jid TEXT NOT NULL);
CREATE TABLE tell_messages_by_sender(
    sender_jid TEXT,
    receiver_jid TEXT,
    messages TEXT[] NOT NULL,
    PRIMARY KEY (sender_jid, receiver_jid)
);

CREATE TABLE ping_group_memberships(
    member_jid TEXT,
    group_name TEXT,
    PRIMARY KEY (member_jid, group_name)
);