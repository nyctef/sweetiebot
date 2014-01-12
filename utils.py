
def is_ping(nickname, message):
    if nickname.lower() in message.lower():
        return True
    else:
        return False


