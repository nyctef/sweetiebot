import logging
import random

def is_ping(nickname, message):
    return nickname.lower() in message.lower()

def is_command(nickname, message):
    return message.lower().strip().startswith(nickname.lower())

def logerrors(func):
    from functools import wraps
    @wraps(func)
    def logged(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception:
            logging.exception('Error in '+func.__name__)
            return "My code is problematic :sweetieoops:"
    return logged

def randomstr():
    return ('%08x' % random.randrange(16**8))

