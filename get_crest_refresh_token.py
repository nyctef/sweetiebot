import argparse
import http.server
import random
import requests
import sys
import threading
import time
import webbrowser
from base64 import b64encode
from pprint import pprint
from urllib.parse import urlparse, parse_qs

import logging
logging.basicConfig(level=logging.DEBUG)

running = True

def get_basic_auth_header(client_id, client_secret):
    return 'Basic ' + b64encode('{}:{}'.format(client_id, client_secret).encode('utf-8')).decode('utf-8')
    
def get_access_token(auth_code):
    global running
    token_url = '{}/token'.format(args.base_url)
    print('token sson url: {}'.format(token_url))
    token_result = requests.post(token_url, data={ 'grant_type' :
        'authorization_code', 'code': auth_code }, headers= { 'Authorization' :
            get_basic_auth_header(args.client_id, args.client_secret) }) 
    result_json = token_result.json()
    pprint(result_json)

    refresh_token = result_json['refresh_token']
    if refresh_token:
        print('\n\n======\nrefresh token: {}\n======\n\n'.format(refresh_token))

    running = False

class HttpHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

        url = urlparse(self.path)
        if url.path == '/favicon.ico':
            print('ignoring favicon')
            return

        qs = parse_qs(url.query)
        pprint(qs)
        if qs['state'] and qs['state'][0] == str(state):
            auth_code = qs['code'][0]
            print('got auth code: {}'.format(auth_code))
            get_access_token(auth_code)

        self.wfile.write(b'ok - you can close this page')

def start_server():
    server = http.server.HTTPServer(('localhost', args.port), HttpHandler)
    server.serve_forever()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Get a CREST refresh token for the specified application')
    parser.add_argument('client_id', help='the application client ID provided by CCP')
    parser.add_argument('client_secret', help='the application client secret provided by CCP')
    parser.add_argument('scopes', help='the scopes required by the application as a space-delimited string')
    parser.add_argument('port', nargs='?', default=51307, help='the port to redirect the oauth request to. The redirect url for the application must be of the form http://localhost:[port]')
    parser.add_argument('base_url', nargs='?', default='https://login.eveonline.com/oauth', help='the base url for eve oauth')

    args = parser.parse_args()

    redirect_url = 'http://localhost:{}'.format(args.port)
    state = random.randint(1, 99999)

    sso_url = '{}/authorize?response_type=code&redirect_uri={}&client_id={}&scope={}&state={}'.format(args.base_url, redirect_url, args.client_id, args.scopes, state)
    print('base sso url: {}'.format(sso_url))

    print('starting http server to handle redirect')
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    print('launching browser with sso_url')
    webbrowser.open(sso_url)

    while running: time.sleep(1)

