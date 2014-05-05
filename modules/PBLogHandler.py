import pushbullet
import logging

class PBLogHandler(logging.Handler):

    def __init__(self, config):
        super(PBLogHandler, self).__init__()
        if (config.pushbullet_api is None or
            config.pushbullet_device is None):
            self.pb = None
            return
        self.pb = pushbullet.Device(config.pushbullet_api,
                                    config.pushbullet_device)

    def emit(self, record):
        if self.pb is not None:
            self.pb.push_note("Sweetiebot", record.message)
