import pushbullet
import logging
import traceback

class PBLogHandler(logging.Handler):

    def __init__(self, config):
        super(PBLogHandler, self).__init__()
        if (config.pushbullet_api is None or
            config.pushbullet_device is None):
            self.pb = None
            return
        pb_api = pushbullet.Pushbullet(config.pushbullet_api)
        pb_devices = pb_api.devices
        pb_device = next(filter(lambda x: x.device_iden == config.pushbullet_device, pb_devices))
        self.pb = pb_device

    def emit(self, record):
        if self.pb is not None:
            try:
                if record.exc_info:
                    title = "Sweetiebot: "+record.message
                    body = ''.join(traceback.format_exception(*record.exc_info))
                else:
                    title = "Sweetiebot error"
                    body = record.message
                self.pb.push_note(title, body)
            except:
                print('exception in PBLogHandler')
                pass
