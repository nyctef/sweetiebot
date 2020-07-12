import random
import logging

log = logging.getLogger(__name__)

class TableList(object):

    def __init__(self, conn, table_name):
        self.cur = conn.cursor()
        self.table_name = table_name
        self.responses = None

    def add_to_file(self, args):
        sql = f"INSERT INTO {self.table_name}(text) VALUES (%s) ON CONFLICT (text) DO NOTHING"
        self.cur.execute(sql, (args.replace('\n', ' ').strip(),))

    def get_next(self):
        if not self.responses:
            log.debug("reading sass file..")
            self.cur.execute(f"SELECT text from {self.table_name}")
            results = self.cur.fetchall()
            self.responses = [x[0].strip() for x in results]
            log.debug(".. read {} responses".format(len(self.responses)))
            random.shuffle(self.responses)
            self.sass_index = -1

        self.sass_index += 1

        if self.sass_index >= len(self.responses):
            log.debug("reshuffling sass")
            random.shuffle(self.responses)
            self.sass_index = 0

        response = self.responses[self.sass_index]
        log.debug("returning response {}: {}".format(self.sass_index, response))
        return response
