import random
import logging

log = logging.getLogger(__name__)

class ResponsesFile(object):

    def __init__(self, filename):
        self.filename = filename
        self.responses = None

    def _remove_dup(self):
        lines_seen = set()  # holds lines already seen
        with open(self.filename, "r") as in_f:
            for line in in_f:
                # not a duplicate
                if line not in lines_seen and not ":lunaglee:" in line:
                    if not any(i in line for i in ('#', '/', '\\')):
                        lines_seen.add(line)
        with open(self.filename, "w") as out_f:
            out_f.writelines(sorted(lines_seen))
        return

    def random_line(self):
        try:
            with open(self.filename, 'r') as f:
                lines = [_f for _f in (line.strip() for line in f) if _f]
                return random.choice(lines)
        except Exception as e:
            log.error("failed to read file "+self.filename+": "+str(e))
            return "/me slaps <target> with a large trout."

    def add_to_file(self, args):
        with open(self.filename, 'ab') as f:
            clean_args = args.replace('\n', ' ')
            log.debug(args)
            log.debug(args.__class__)
            f.write((clean_args + '\n').encode('utf-8'))
        self._remove_dup()

    def get_next(self):
        if not self.responses:
            log.debug("reading sass file..")
            with open(self.filename, 'r') as f:
                self.responses = [line.strip() for line in f.readlines()]
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
