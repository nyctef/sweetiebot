import re
import random

class SweetieMarkov(object):
    """Generate markov-style random chat from input text.

    Uses ideas based on http://megahal.alioth.debian.org/How.html but a custom
    implementation. It tries to be cleverer with input splitting, and the way
    it gets started from a single keyword into the full chain is a bit hacky"""

    separator = '\x01'
    begin = '\x02'
    end = '\x03'
    word_re = re.compile(r'^[a-zA-Z\-\']+$')
    emote_re = re.compile(r'^:[a-zA-Z0-9]+:$')
    punctuation = frozenset((',', '.', ':', ';', '!', '?', '~', '(', ')'))
    order = 4

    def __init__(self, redis, banned_keywords, preferred_keywords, swap_words):
        self.redis = redis
        self.banned_keywords = frozenset(self.read_banned_keywords(
            banned_keywords) + list(self.punctuation))
        self.preferred_keywords = []#frozenset(preferred_keywords)
        self.swap_words = self.read_swap_words(swap_words)

    def store_message(self, message):
        split_message = self.split_message(message)
        split_message = map(lambda x: x.lower(), split_message)
        split_message = [self.begin] + split_message + [self.end]
        #print('split_message', split_message)
        #keywords = self.extract_keywords(split_message)
        #print('keywords', list(keywords))
        main_sequences = list(self.get_subsequences(split_message, self.order+1))
        keyword_sequences_fwd = list(self.get_keyword_sequences(split_message, self.order+1, True))
        keyword_sequences_bwd = list(self.get_keyword_sequences(split_message, self.order+1, False))
        self.store_sequences(main_sequences)
        for seq in keyword_sequences_fwd:
            self.store_sequence('fwd', seq)
        for seq in keyword_sequences_bwd:
            self.store_sequence('bwd', seq)
        #replaced_message = self.replace_swap_words(split_message)
        ##print(replaced_message)

    def store_sequences(self, sequences):
        for seq in sequences:
            self.store_sequence('fwd', seq)
            bwd = list(reversed(seq))
            self.store_sequence('bwd', bwd)

    def store_sequence(self, prefix, sequence):
        key = 'seq'+prefix+self.separator.join(sequence[:-1])
        #print prefix, sequence, sequence.__class__
        self.redis.hincrby(key, sequence[-1], 1)

    def extract_keywords(self, sequence):
        return filter(lambda x: self.is_keyword(x), sequence)

    def is_keyword(self, segment):
        return (self.word_re.match(segment) and
            segment.lower() not in self.banned_keywords)

    def split_message(self, message):
        initial_split = message.split()
        #print('initial_split', initial_split)
        split = list(self.split_words(initial_split))
        #print('segment split', split)
        return split

    def replace_swap_words(self, split_message):
        for word in split_message:
            if word in self.swap_words.keys():
                yield self.swap_words[word]
            else:
                yield word

    def get_keyword_sequences(self, sequence, subsequence_length, fwd=True):
        """ We need a list of shorter sequences since we start with a single
        keyword input and most of our data requires four segments as an input"""
        for idx, segment in enumerate(sequence):
            if not self.is_keyword(segment):
                continue
            for length in range(2, subsequence_length):
                for subseq in self.get_subsequences_at(sequence, length, idx, fwd):
                    if len(subseq)>1:
                        yield subseq

    def get_subsequences(self, sequence, subsequence_length):
        for i in range(len(sequence) - subsequence_length + 1):
            yield sequence[i:i+subsequence_length]

    def get_subsequences_at(self, sequence, subsequence_length, position, fwd):
        #print('getting subseqs at', position, subsequence_length, sequence[position])
        direction = 1 if fwd else -1
        position_diff = position + (subsequence_length * direction)
        yield sequence[position:position_diff]
        yield sequence[position:position_diff:-1]

    def split_words(self, initial_split):
        for segment in initial_split:
            if self.word_re.match(segment) or self.emote_re.match(segment):
                yield segment
                yield ' '
            elif (segment[0] in self.punctuation
                and self.word_re.match(segment[1:])):
                yield segment[0] + ' '
                yield segment[1:]
            elif (segment[-1] in self.punctuation
                  and self.word_re.match(segment[:-1])):
                yield segment[:-1]
                yield segment[-1] + ' '
            elif (segment[-1] in self.punctuation
                  and segment[0] in self.punctuation
                  and self.word_re.match(segment[1:-1])):
                yield segment[0] + ' '
                yield segment[1:-1]
                yield segment[-1] + ' '

    def get_message(self, input_message):
        best = set()
        potentials = set()
        for x in xrange(100):
            potential_keyword, potential_message = self.generate_potential_message(input_message)
            #print 'potential', potential_message
            if (potential_message[0] == self.begin and
                potential_message[-1] == self.end and
                len(potential_message) > 5):
                best.add((potential_keyword, tuple(potential_message)))
            else:
                potentials.add((potential_keyword, tuple(potential_message)))
        if best:
            print('we got a best!')
            result = self.set_random_choice(best)
        else:
            result = self.set_random_choice(potentials)
        keyword, message = result
        print('using keyword', keyword)
        return ''.join(message[1:-1])

    def set_random_choice(self, the_set):
        return random.sample(the_set, 1)[0]

    def generate_potential_message(self, input_message):
        #print('input_message', input_message)
        split_message = self.split_message(input_message)
        split_message = self.replace_swap_words(split_message)
        #print('split_message', split_message)
        keywords = self.extract_keywords(split_message)
        keyword = random.choice(keywords)
        forwards = self.generate_message_from_keyword(keyword, 'fwd')
        #print('forwards', forwards)
        backwards = list(reversed(self.generate_message_from_keyword(keyword, 'bwd')))[:-1]
        #print('backwards', backwards)
        return keyword, backwards + forwards

    def generate_message_from_keyword(self, keyword, prefix):
        sequence = [keyword]
        terminator = self.end if prefix == 'fwd' else self.begin
        for x in range(3):
            #print(sequence)
            next = self.get_next_in_sequence(sequence, prefix)
            if next is None:
                break
            sequence = sequence + [next]
            if next == terminator:
                break

        for x in range(50):
            #print('initial key', sequence[-4:])
            next = self.get_next_in_sequence(sequence[-4:], prefix)
            if next is None:
                break
            sequence = sequence + [next]
            if next == terminator:
                break

        return sequence

    def get_next_in_sequence(self, sequence, prefix):
        key = 'seq'+prefix+self.separator.join(sequence)
        if not self.redis.exists(key):
            #print('key not found', key)
            return None
        nexts = self.redis.hgetall(key)
        return self.weighted_choice(list(nexts.iteritems()))

    def weighted_choice(self, choices):
        """taken from http://stackoverflow.com/a/3679747/895407"""
        total = sum(int(w) for c, w in choices)
        r = random.uniform(0, total)
        upto = 0
        for c, w in choices:
            if upto + int(w) > r:
                return c
            upto += int(w)
        assert False, "Shouldn't get here"

    def read_swap_words(self, filename):
        with open(filename, 'r') as f:
            # read all non-comment lines
            lines = filter(lambda x: x[0]!='#', f.readlines())
            lines = map(lambda x: x.lower(), lines)
            # split each line and convert to dictionary
            return {l[0]:l[1] for l in map(lambda x: x.strip().split(), lines)}

    def read_banned_keywords(self, filename):
        with open(filename, 'r') as f:
            lines = filter(lambda x: x[0]!='#', f.readlines())
            lines = map(lambda x: x.lower().strip(), lines)
            return lines


