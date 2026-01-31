
from .session import Session
from ..utils.OrderedList import OrderedList
from ..utils.Types import PRODUCT,VARIETY,TRANSACTION_TYPE,ORDER_TYPE,VALIDITY,EXCHANGE,INTERVAL
from .websocket_connection.ticker import Ticker
from datetime import datetime,date,time,timedelta


class Trader:
    def __init__(self,user_name,password,totp_key) -> None:
        '''
        This Trader is the way to start the Process, the param cred_dict requires ["user_name","password","totp_key"]

        The "totp_key" can be extracted when creating the two factor authentication in the kite app, click on the QR code and use the same key.
        '''
        self.session = Session(user_name,password,totp_key)
        self.instruments = self.session.instruments
        self.instrument_details = self.session.ins_details_cache
        self.ticker = None
        self.startTicker()
    
    def format_date(self,value):
        if isinstance(value,str):
            return value
        elif isinstance(value,datetime):
            return str(value.date())
        elif isinstance(value,date):
            return str(value)
        else:
            raise Exception('expected value types are ["str", "datetime", "date"]\nthe type of value provided is {}'.format(type(value)))
    
    def historical_data(self,instrument_token,start_date,end_date,interval='5minute'):
        url = 'https://kite.zerodha.com/oms/instruments/historical/{}/{}'.format(instrument_token,interval)
        params = {
            'user_id': self.session.user_name,
            'oi': '1',
            'from': self.format_date(start_date),
            'to': self.format_date(end_date),
        }
        response = self.session.request(url=url,method=Session.TYPE_GET,params=params)
        if response['status'] == 'success':
            return OrderedList(response['data']['candles'])
        else:
            raise Exception(response['message'])
    
    def get_orders(self):
        url = 'https://kite.zerodha.com/oms/orders'
        response = self.session.request(url=url,method=Session.TYPE_GET)
        if response['status'] == 'success':
            return response['data']
        else:
            raise Exception(response['message'])
    
    def get_positions(self):
        url = 'https://kite.zerodha.com/oms/portfolio/positions'
        response = self.session.request(url=url,method=Session.TYPE_GET)
        if response['status'] == 'success':
            return response['data']
        else:
            raise Exception(response['message'])
        
    
    def get_holdings(self):
        url = 'https://kite.zerodha.com/oms/portfolio/holdings'
        response = self.session.request(url=url,method=Session.TYPE_GET)
        if response['status'] == 'success':
            return response['data']
        else:
            raise Exception(response['message'])
    
    def get_margins(self):
        url = 'https://kite.zerodha.com/oms/user/margins'
        response = self.session.request(url=url,method=Session.TYPE_GET)
        if response['status'] == 'success':
            return response['data']
        else:
            raise Exception(response['message'])
    
    def get_profile(self):
        url = 'https://kite.zerodha.com/oms/user/profile/full'
        response = self.session.request(url=url,method=Session.TYPE_GET)
        if response['status'] == 'success':
            return response['data']
        else:
            raise Exception(response['message'])
    
    def check_app_sessions(self):
        url = 'https://kite.zerodha.com/api/user/app_sessions'
        response = self.session.request(url=url,method=Session.TYPE_GET)
        if response['status'] == 'success':
            return response['data']
        else:
            raise Exception(response['message'])
    
    def place_order(self,symbol,exchange,transaction_type,quantity,
                    variety=VARIETY.REGULAR,
                    product=PRODUCT.CNC,
                    order_type=ORDER_TYPE.MARKET,
                    validity=VALIDITY.DAY,
                    price='0',
                    disclosed_quantity='0',
                    trigger_price='0',
                    squareoff='0',
                    stoploss='0',
                    trailing_stoploss='0'):
        payload = {
            'variety': variety,
            'exchange': exchange,
            'tradingsymbol': symbol,
            'transaction_type': transaction_type,
            'order_type': order_type,
            'quantity': quantity,
            'price': price,
            'product': product,
            'validity': validity,
            'disclosed_quantity': disclosed_quantity,
            'trigger_price': trigger_price,
            'squareoff': squareoff,
            'stoploss': stoploss,
            'trailing_stoploss': trailing_stoploss,
            'user_id': self.session.user_name
        }
        url = 'https://kite.zerodha.com/oms/orders/regular'
        response = self.session.request(url=url,method=Session.TYPE_POST,data=payload)
        if response['status'] == 'success':
            return response['data']
        elif response['status'] == 'error':
            raise Exception(response['message'])

    def startTicker(self):
        self.ticker = Ticker(session=self.session)
    
    def get_bnf_expiries(self):
        return list(self.instruments['derivatives']['BANKNIFTY']['derivatives'].keys())

    def get_expiries(self,derivative_name):
        return list(self.instruments['derivatives'][derivative_name]['derivatives'].keys())
    
    def get_derivatives_list(self):
        return list(self.instruments['derivatives'].keys())
    
    def get_strikes(self,derivative_name,expiry):
        return list(self.instruments['derivatives'][derivative_name]['derivatives'][expiry]['options'].keys())

    def get_current_expiries_strikes(self,derivative_name):
        current_expiry = self.get_expiries(derivative_name)
        return self.instruments['derivatives'][derivative_name]['derivatives'][current_expiry[0]]['options']
    
    def get_bnf_current_expiry_strikes(self):
        current_expiry = self.get_bnf_expiries()
        return self.instruments['derivatives']['BANKNIFTY']['derivatives'][current_expiry[0]]['options']
    
    def get_instrument_token_equity(self,symbol):
        symbol = symbol.upper()
        try:
            instrument = self.instruments['underlyer_list']['NSE']['NSE']['EQ'][symbol]
        except KeyError:
            raise Exception(f'{symbol} not found in the list of instruments list, please check the symbol correctly again')
        return {'tradingsymbol': instrument['tradingsymbol'],'instrument_token': instrument['instrument_token']}

    def get_instrument_token_option(self,symbol,expiry,strike,strike_type,no_check=False):
        def check(strike):
            if type(strike) == int:
                strike = '{}.0'.format(strike)
            elif type(strike) == float:
                strike = '{}.0'.format(int(strike))
            elif type(strike) == str:
                if strike[-2:] == '.0':
                    strike = strike
                else:
                    strike = '{}.0'.format(int(strike))
            return strike
        
        symbol = symbol.upper()
        strike = check(strike)
        strike_type = strike_type.upper()
        if not no_check:
            try:
                instrument = self.instruments['derivatives'][symbol]
            except KeyError:
                raise Exception(f'{symbol} not found in the list of instruments list, please check the symbol correctly again')
            try:
                instrument = instrument['derivatives'][expiry]
            except KeyError:
                raise Exception(f'{expiry} not found in the list of {symbol} instruments list, please check the symbol correctly again')
            try:
                instrument = instrument['options'][strike]
            except KeyError:
                raise Exception(f'{strike} not found in the expiry list ({expiry}) of {symbol} instruments list, please check the symbol correctly again')
            try:
                instrument = instrument[strike_type]
            except KeyError:
                raise Exception(f'please check strike type')
            return {'tradingsymbol': instrument['tradingsymbol'],'instrument_token': instrument['instrument_token']}
        else:
            ts = self.instruments['derivatives'][symbol]['derivatives'][expiry]['options'][strike][strike_type]['tradingsymbol']
            insToken = self.instruments['derivatives'][symbol]['derivatives'][expiry]['options'][strike][strike_type]['instrument_token']
            return {'tradingsymbol': ts,'instrument_token': insToken}

    def get_instrument_token_index(self,symbol):
        symbol = symbol.upper()
        try:
            try:
                instrument = self.instruments['underlyer_list']['NSE']['NSE-INDICES']['EQ'][symbol]
            except:
                instrument = self.instruments['underlyer_list']['BSE']['BSE-INDICES']['EQ'][symbol]
        except KeyError:
            raise Exception(f'{symbol} not found in the list of instruments list, please check the symbol correctly again')
        return {'tradingsymbol': instrument['tradingsymbol'],'instrument_token': instrument['instrument_token']}
    
    def get_instrument_token_future(self,symbol,expiry):
        symbol = symbol.upper()
        try:
            instrument = self.instruments['derivatives'][symbol]
        except KeyError:
            raise Exception(f'{symbol} not found in the list of instruments list, please check the symbol correctly again')
        try:
            instrument = instrument['derivatives'][expiry]
        except KeyError:
            raise Exception(f'{expiry} not found in the list of {symbol} instruments list, please check the symbol correctly again')
        return {'tradingsymbol': instrument['tradingsymbol'],'instrument_token': instrument['instrument_token']}

    def get_previous_data(self,instrument_token,days=0,interval=INTERVAL.MINUTE_15):
        today = datetime.now()
        start_date = today - timedelta(days=days)
        return self.historical_data(instrument_token=instrument_token,start_date=start_date,end_date=today,interval=interval)
    
    def get_todays_data(self,instrument_token):
        current_day = datetime.now().date()
        return self.historical_data(instrument_token=instrument_token,start_date=current_day,end_date=current_day,interval=INTERVAL.MINUTE_15)
    