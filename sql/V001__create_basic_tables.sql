CREATE TABLE IF NOT EXISTS deowl_fails(id serial PRIMARY KEY, text TEXT);
ALTER TABLE deowl_fails ADD UNIQUE (text);

CREATE TABLE IF NOT EXISTS actions(id serial PRIMARY KEY, text TEXT);
ALTER TABLE actions ADD UNIQUE (text);

CREATE TABLE IF NOT EXISTS cadmusic(id serial PRIMARY KEY, text TEXT);
ALTER TABLE cadmusic ADD UNIQUE (text);

CREATE TABLE IF NOT EXISTS sass(id serial PRIMARY KEY, text TEXT);
ALTER TABLE sass ADD UNIQUE (text);
