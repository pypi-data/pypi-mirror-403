import time
import websocket
import json
from datetime import datetime
import threading
from ...utils.parsing import encodeURIComponent,parse_binary
from ...utils.Types import MODE_STRING,KEYS
from typing import Union, List
import os
import certifi

class Ticker:
    def __init__(self,session):
        self.__private_session = session
        self.__private_input_message = None
        self.__private_websocket_connection = None
        self.connect_to_websocket()
        self.last_msg = None
        self.last_msg_time = None
        print('ticker done')

    def connect_to_websocket(self):
        self.params = {
            'api_key': 'kitefront',
            'user_id': self.__private_session.user_name,
            'enctoken': encodeURIComponent(self.__private_session._enc_token),
            'uid': f'{int(time.time() * 1000)}',
            'user-agent': 'kite3-web',
            'version': '3.0.0',
        }
        address = "wss://ws.zerodha.com/"
        url = self.params_to_url(address)
        if os.environ.get('WEBSOCKET_CLIENT_CA_BUNDLE') is None:
            os.environ['WEBSOCKET_CLIENT_CA_BUNDLE'] = certifi.where()
        ws = websocket.WebSocketApp(url, on_message=self.on_message,on_error=self.on_error,on_close=self.on_close)
        ws.on_open = self.on_open
        self.__private_websocket_connection = ws
        thread = threading.Thread(target=ws.run_forever,daemon=True)
        thread.start()
        print(f'connection successful')

        
    
    def params_to_url(self,base_url):
        url_params = '&'.join([f"{key}={value}" for key, value in self.params.items()])
        return f"{base_url}?{url_params}"
    
    def on_message(self,ws, message):
        self.last_msg = parse_binary(message)
        self.last_msg_time = datetime.now()
        #print(parse_binary(message))

    def on_error(self,ws, error):
        print(error)

    def on_close(self,ws):
        print("### closed ###")
    
    def on_open(self,ws):
        m1 = {"a": KEYS.subscribe ,"v":[256265,260105]}
        m2 = {"a": KEYS.mode,"v":[ MODE_STRING.modeLTPC ,[256265,260105]]}
        ws.send(json.dumps(m1))
        ws.send(json.dumps(m2))
    
    def send_message(self,message):
        self.__private_websocket_connection.send(json.dumps(message))
    
    def subscribe(self, tokens: Union[List[int], int],mode=MODE_STRING.modeLTPC):
        token_type = type(tokens)
        if not (token_type == list or token_type == int):
            raise Exception('tokens need to be in a list of integers or just an integer, \nexample 1:- [256265,260105]\nCurrent Type:{}'.format(type(tokens)))
        if token_type == list:
            m1 = {"a": KEYS.subscribe ,"v":tokens}
            m2 = {"a": KEYS.mode,"v":[ mode ,tokens]}
            self.send_message(m1)
            self.send_message(m2)
        elif token_type == int:
            m1 = {"a": KEYS.subscribe ,"v":[tokens]}
            m2 = {"a": KEYS.mode,"v":[ mode ,[tokens]]}
            self.send_message(m1)
            self.send_message(m2)

    def unsubscribe(self, tokens: Union[List[int], int]):
        token_type = type(tokens)
        if not (token_type == list or token_type == int):
            raise Exception('tokens need to be in a list of integers or just an integer, \nexample 1:- [256265,260105]\nCurrent Type:{}'.format(type(tokens)))
        if token_type == list:
            m1 = {"a": KEYS.unsubscribe ,"v":tokens}
            self.send_message(m1)
        elif token_type == int:
            m1 = {"a": KEYS.unsubscribe ,"v":[tokens]}
            self.send_message(m1)