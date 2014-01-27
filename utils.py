import logging

def is_ping(nickname, message):
    if nickname.lower() in message.lower():
        return True
    else:
        return False


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

