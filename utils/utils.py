import logging
import random

def logerrors(func):
    from functools import wraps
    @wraps(func)
    def logged(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception:
            print('\n\n####\n\n')
            logging.exception('Error in '+func.__name__)
            print('\n\n####\n\n')
            return "My code is problematic :sweetieoops:"
    return logged

def randomstr():
    return ('%08x' % random.randrange(16**8))

def botcmd(*args, **kwargs):
    """Decorator for bot command functions
    based on http://sourceforge.net/p/pythonjabberbot/code/ci/master/tree/jabberbot.py
    """
    def decorate(func, hidden=False, name=None, thread=False):
        setattr(func, '_bot_command', True)
        setattr(func, '_bot_command_hidden', hidden)
        setattr(func, '_bot_command_name', name or func.__name__)
        return func
    if len(args):
        return decorate(args[0], **kwargs)
    else:
        return lambda func: decorate(func, **kwargs)

