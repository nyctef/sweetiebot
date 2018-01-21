import random
import logging

log = logging.getLogger(__name__)

class ResponsesFile(object):

    def __init__(self, filename):
        self.filename = filename
        self.responses = None

    def _open(self, mode):
        return open(self.filename, mode, encoding="utf-8", newline='')

    def _read(self):
        return self._open("r")

    def _write(self):
        return self._open("w")

    def _append(self):
        return self._open("a")

    def _remove_dup(self):
        lines_seen = set()  # holds lines already seen
        with self._read() as in_f:
            for line in in_f:
                # not a duplicate
                if line not in lines_seen and not ":lunaglee:" in line:
                    lines_seen.add(line)
        with self._write() as out_f:
            out_f.writelines(sorted(lines_seen))
        return

    def random_line(self):
        try:
            with self._read() as f:
                lines = [_f for _f in (line.strip() for line in f) if _f]
                return random.choice(lines)
        except Exception as e:
            log.error("failed to read file "+self.filename+": "+str(e))
            return "/me slaps <target> with a large trout."

    def add_to_file(self, args):
        with self._append() as f:
            args = args.replace('\n', ' ') + '\n'
            log.info('adding %r to %s', args, self.filename)
            f.write(args)
        self._remove_dup()

    def get_next(self):
        if self.next_response:
            response = self.next_response
            self.next_response = None
            return response
            
        if not self.responses:
            log.debug("reading sass file..")
            with self._read() as f:
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
    
    def pick_line(self, line_number, sender):
        log.debug("{} forced next sass line {}.".format(sender, line_number))
        with self._read() as f:
            responses_list = [line.strip() for line in f.readlines()]
            log.debug(".. read {} responses".format(len(responses_list)))

        if not line_number > len(responses_list) and not line_number < 1:
            self.next_response = responses_list[line_number - 1]
            return True
        else:
            return False
