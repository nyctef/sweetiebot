from azure.servicebus import ServiceBusService, Message
import logging

log = logging.getLogger(__name__)

class SweetieMQ(object):

    bus_service = None
    topic = None

    def __init__(self, config):
        account_key = getattr(config, 'sb_account_key', None)
        if account_key is None:
            log.warn('sb_account_key is not set, skipping mq setup')
            return

        issuer = getattr(config, 'sb_issuer', 'owner')
        service_namespace = getattr(config, 'sb_namespace', 'jabber-messages')
        topic = getattr(config, 'sb_topic', 'test-topic')

        self.bus_service = ServiceBusService(service_namespace=service_namespace,\
                account_key=account_key, issuer=issuer)
        self.topic = topic

    def send(self, message):
        if self.bus_service is None:
            return
        log.debug('Sending message '+str(message))
        msg = Message(message)
        try:
            self.bus_service.send_topic_message(self.topic, msg)
        except Exception as e:
            log.error("MESSAGE DELIVERY FAILED: "+str(e))
