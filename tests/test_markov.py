# add parent dir to path since we're not using any fancy frameworks for
# these tests
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)

from modules import SweetieMarkov, SweetieRedis, FakeRedis

class StubBot(object):
    def load_commands_from(self, target):
        pass

def read_dump():
    """open an input file with one message per line"""
    with open('output.txt', 'r') as f:
        return f.readlines()

if __name__ == '__main__':
    lines = read_dump()
    markov = SweetieMarkov(StubBot(), SweetieRedis(FakeRedis()))
    for line in lines:
        markov.store_message(line)
    while True:
        seed = raw_input("Enter a seed: ")
        print markov.get_message(seed)
