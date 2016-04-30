import logging
import requests
from base64 import b64encode
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

class SweetieCrest:
    def __init__(self, base_url, client_id, client_secret, refresh_token):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.bearer_token = None
        self.bearer_token_age = datetime(1, 1, 1)

    def get(self, endpoint):
        url = self.base_url + endpoint
        log.info(url)
        if datetime.now() - self.bearer_token_age > timedelta(minutes=20):
            self.get_new_bearer_token()
        return requests.get(url, headers={
            'Authorization':'Bearer '+self.bearer_token
            })

    def get_basic_auth_header(self, client_id, client_secret):
        return 'Basic ' + b64encode('{}:{}'.format(client_id, client_secret).encode('utf-8')).decode('utf-8')

    def get_new_bearer_token(self):
        auth = self.get_basic_auth_header(self.client_id, self.client_secret)
        log.info('requesting new access token')
        result = requests.post('https://login.eveonline.com/oauth/token',
            data={'grant_type':'refresh_token', 'refresh_token':self.refresh_token},
            headers={'Authorization': auth})
        log.info(result.text)
        json = result.json()
        if 'error_description' in json.keys():
            raise Exception('crest error: '+str(json['error_description']))
        self.bearer_token = json['access_token']
        self.bearer_token_age = datetime.now()



