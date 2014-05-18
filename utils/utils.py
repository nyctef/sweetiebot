import logging
import random

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

