from azure.servicebus import ServiceBusService, Message

class SweetieMQ:

    def __init__(self, account_key, issuer):
        self.bus_service = ServiceBusService(service_namespace='jabber-fimsquad',\
                account_key=account_key, issuer=issuer)
        self.topic = 'chat-general'

    def send(self, message):
        msg = Message(message)
        try:
            self.bus_service.send_topic_message(self.topic, msg)
        except Exception as e:
            print("MESSAGE DELIVERY FAILED: "+str(e))
