import re
import random
import logging
log = logging.getLogger(__name__)

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
        split_message = [x.lower() for x in split_message]
        split_message = [self.begin] + split_message + [self.end]
        #log.info('split_message', split_message)
        #keywords = self.extract_keywords(split_message)
        #log.info('keywords', list(keywords))
        main_sequences = list(self.get_subsequences(split_message, self.order+1))
        keyword_sequences_fwd = list(self.get_keyword_sequences(split_message, self.order+1, True))
        keyword_sequences_bwd = list(self.get_keyword_sequences(split_message, self.order+1, False))
        self.store_sequences(main_sequences)
        for seq in keyword_sequences_fwd:
            self.store_sequence('fwd', seq)
        for seq in keyword_sequences_bwd:
            self.store_sequence('bwd', seq)
        #replaced_message = self.replace_swap_words(split_message)
        ##log.info(replaced_message)

    def store_sequences(self, sequences):
        for seq in sequences:
            self.store_sequence('fwd', seq)
            bwd = list(reversed(seq))
            self.store_sequence('bwd', bwd)

    def store_sequence(self, prefix, sequence):
        key = 'seq'+prefix+self.separator.join(sequence[:-1])
        #log.info prefix, sequence, sequence.__class__
        self.redis.hincrby(key, sequence[-1], 1)

    def extract_keywords(self, sequence):
        return [x for x in sequence if self.is_keyword(x)]

    def is_keyword(self, segment):
        return (self.word_re.match(segment) and
            segment.lower() not in self.banned_keywords)

    def split_message(self, message):
        initial_split = message.split()
        #log.info('initial_split', initial_split)
        split = list(self.split_words(initial_split))
        #log.info('segment split', split)
        return split

    def replace_swap_words(self, split_message):
        for word in split_message:
            if word in list(self.swap_words.keys()):
                yield self.swap_words[word]
            else:
                yield word

    def get_keyword_seed_subsequences(self, sequence):
        current_keyword_chain = []
        for segment in sequence:
#            log.debug('looking at %s', segment)
            if not (self.is_keyword(segment)
                    or segment.isspace()
                    or segment.strip() in self.punctuation):
#                log.debug('resetting on segment')
                current_keyword_chain = []
                continue
            if (not len(current_keyword_chain)) and segment.isspace():
#                log.debug('we dont want to start the sequence with %s', segment)
                continue
            current_keyword_chain.append(segment)
            if not segment.isspace():
                yield tuple(current_keyword_chain[-4:])

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
        #log.info('getting subseqs at', position, subsequence_length, sequence[position])
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
        potentials = set()
        for x in range(200):
            potential_keyword, potential_message = self.generate_potential_message(input_message)
            if potential_message is None: continue
            potential_score = self.score_message(input_message, potential_message)
            potentials.add((potential_keyword, potential_score, tuple(potential_message)))
        result = None
        high_score = 0
        for p in potentials:
            log.info(p)
            if p[1] > high_score:
                result = p
        if result is None:
            return None
        keyword, score, message = result
        log.info('using keyword %s ', keyword)
        return ''.join(message[1:-1])

    def score_message(self, input_message, potential_message):
        if not potential_message:
            return 0
        log.debug('scoring %s', potential_message)
        input_message_split = self.split_message(input_message)
        score = 0
        # we should get messages with a size roughly matching the input
        score -= abs(len(input_message_split) - len(potential_message)) * 20
        log.debug('input len %s', len(input_message_split))
        log.debug('output len %s', len(potential_message))
        log.debug('after length penalty: %s', score)

        # we prefer messages that start and end at expected points
        if (potential_message[0] == self.begin and
            potential_message[-1] == self.end):
            score += 100
        log.debug('after begin/end bonus: %s', score)


        # we really don't like parrotting the user
        if self.message_is_subset_of_input(input_message_split,
                                           potential_message):
            score -= 1000
        log.debug('after parrot penalty: %s', score)

        # however, we do like talking about the same things they do
        common_keywords = self.get_common_keywords(input_message_split,
                                                   potential_message)
        # let's try and get at least another common keyword
        if len(common_keywords) < 2:
            score -= 1000
        else:
            score += 100 * len(common_keywords)
        log.debug('after keyword bonus: %s', score)

        return score

    def get_common_keywords(self, input_message_split, potential_message):
        return (set(self.extract_keywords(input_message_split)) &
                set(self.extract_keywords(potential_message)))

    def message_is_subset_of_input(self, input_message_split, potential_message):
        potential_except_punc = self.only_words(set(potential_message))
        input_except_punc = self.only_words(set(input_message_split))
#        log.info('comparing %s against %s', potential_except_punc,
#                 input_except_punc)
        return potential_except_punc.issubset(input_except_punc)

    def only_words(self, word_set):
        return set([x for x in word_set if self.word_re.match(x)])

    def set_random_choice(self, the_set):
        return random.sample(the_set, 1)[0]

    def generate_potential_message(self, input_message):
        #log.info('input_message', input_message)
        split_message = self.split_message(input_message)
        split_message = self.replace_swap_words(split_message)
        #log.info('split_message', split_message)
        keywords = tuple(self.get_keyword_seed_subsequences((split_message)))
        log.info('potential keywords %s', keywords)
        if not keywords:
            return None, None
        keyword = random.choice(keywords)
        forwards = self.generate_message_from_keyword(keyword, 'fwd')
        #log.info('forwards', forwards)
        backwards = list(reversed(self.generate_message_from_keyword(keyword, 'bwd')))[:-len(keyword)]
        #log.info('backwards', backwards)
        return keyword, backwards + forwards

    def generate_message_from_keyword(self, keywords, prefix):
        sequence = list(keywords)
        terminator = self.end if prefix == 'fwd' else self.begin

        for x in range(50):
            #log.info('initial key', sequence[-4:])
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
            #log.info('key not found', key)
            return None
        nexts = self.redis.hgetall(key)
        return self.weighted_choice(list(nexts.items()))

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
            lines = [x for x in f.readlines() if x[0]!='#']
            lines = [x.lower() for x in lines]
            # split each line and convert to dictionary
            return {l[0]:l[1] for l in [x.strip().split() for x in lines]}

    def read_banned_keywords(self, filename):
        with open(filename, 'r') as f:
            lines = [x for x in f.readlines() if x[0]!='#']
            lines = [x.lower().strip() for x in lines]
            return lines


