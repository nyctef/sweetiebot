import requests
import time
import datetime
import logging
import feedparser
from utils import logerrors
from modules.MessageResponse import MessageResponse

log = logging.getLogger(__name__)

def get_watcher(atom_url):
    watcher = AtomWatcher(atom_url)
    watcher.get_next()
    return watcher

class AtomWatcher:
    def __init__(self, atom_url):
        self.atom_url = atom_url
        self.latest_entry_id = None

    def get_next(self):
        try:
            should_return = self.latest_entry_id is not None

            log.debug('downloading {}'.format(self.atom_url))
            feed = feedparser.parse(self.atom_url)
            if not 'status' in feed or feed.status >= 400:
                log.warning('Error downloading feed {}: {}'.format(self.atom_url, feed))
                return None
            title = feed.feed.title
            if not feed.entries: 
                log.error('found 0 entries in feed {}'.format(self.atom_url))
                return None
            # TODO: assuming entries[0] will always be the latest - is this true?
            entry = feed.entries[0]
            if entry.id != self.latest_entry_id:
                log.debug('updating to entry id {}'.format(entry.id))
                self.latest_entry_id = entry.id
                link = next((l.href for l in entry.links if l.rel == 'alternate'), None)
                text = entry.title
                html = '{}: <a href="{}">{}</a>'.format(title, link, text)
                plain = '{}: {} [ {} ]'.format(title, text, link)
                log.debug((html, plain))
                if should_return:
                    log.debug('sending...')
                    return MessageResponse(plain, None, html=html)
            else:
                log.debug('entry id {} matches previously seen id, skipping'.format(entry.id))
        except Exception as e:
            log.exception('Error pulling feed from atom')


