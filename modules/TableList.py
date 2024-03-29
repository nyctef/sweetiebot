import random
import logging

log = logging.getLogger(__name__)


class TableList(object):
    def __init__(self, dbwrapper, table_name):
        self.dbwrapper = dbwrapper
        self.table_name = table_name
        self.responses = None

    def add_line(self, line):
        sql = f"INSERT INTO {self.table_name}(text) VALUES (%s) ON CONFLICT (text) DO NOTHING"
        self.dbwrapper.write(sql, (line,))

    def read_all(self):
        results = self.dbwrapper.query_all(f"SELECT text from {self.table_name}")
        return [x[0].strip() for x in results]


class RandomizedList(object):
    def __init__(self, storage):
        self.storage = storage
        self.responses = None

    def add_line(self, line):
        self.storage.add_line(line)

    def get_next(self):
        log.debug("RandomizedList get_next")
        if not self.responses:
            log.debug("reading response list..")
            self.responses = self.storage.read_all()
            log.debug(".. read {} responses".format(len(self.responses)))
            random.shuffle(self.responses)
            self.sass_index = -1

        self.sass_index += 1

        if self.sass_index >= len(self.responses):
            log.debug("reshuffling sass")
            self.responses = self.storage.read_all()
            random.shuffle(self.responses)
            self.sass_index = 0

        response = self.responses[self.sass_index]
        log.debug("returning response {}: {}".format(self.sass_index, response))
        return response
