import random

class ResponsesFile(object):

    def __init__(self, filename):
        self.filename = filename
        self.responses = None

    def _remove_dup(self):
        lines_seen = set()  # holds lines already seen
        in_f = open(self.filename, "r")
        for line in in_f:
            # not a duplicate
            if line not in lines_seen and not ":lunaglee:" in line:
                if not any(i in line for i in ('#', '/', '\\')):
                    lines_seen.add(line)
        in_f.close()
        out_f = open(self.filename, "w")
        out_f.writelines(sorted(lines_seen))
        out_f.close()
        return


    def random_line(self):
        try:
            with open(self.filename, 'r') as f:
                lines = filter(None, (line.strip() for line in f))
                return random.choice(lines)
        except Exception as e:
            print("failed to read file "+self.filename+": "+str(e))
            return "/me slaps <target> with a large trout."

    def add_to_file(self, args):
        f = open(self.filename, 'a')

        clean_args = args.replace('\n', ' ')
        f.write(clean_args + '\n')
        f.close()
        self._remove_dup()

    def get_next(self):
        if not self.responses:
            print("reading sass file..")
            with open(self.filename, 'r') as f:
                self.responses = [line.strip() for line in f.readlines()]
                random.shuffle(self.responses)
            self.sass_index = -1
        self.sass_index += 1
        response = self.responses[self.sass_index]
        return response
