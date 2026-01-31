# Zern Class Documentation

This is a free library. This doesn't require any subscription to use. 

### __Disclaimer: Please dont overload the server.__

## INSTALLATION

1) get it the pip way 
```
pip install zern
```

2) build from here using build tool
```
git clone https://github.com/ExBlacklight/Zern.git
cd Zern
pip install build
python -m build
pip install "./dist/zern-0.0.18.tar.gz"
```

**You can convert the inbuilt DataFrame to pandas. check it in the "INBUILT DATAFRAME" Section below.**

## SAMPLE SCRIPTS

1) download data

```python
from zern import Trader
from credentials import user_name, password, totp_key

#initiate trader
trader = Trader(user_name=user_name,password=password,totp_key=totp_key)

#retrieve 'INFOSYS' insrtrument token and get previous 10 days data
token = trader.get_instrument_token_equity('infy')
insToken = token['instrument_token']
df = trader.get_previous_data(insToken,days=10)

trader

# save the data 
df.save('infy.dict')
```

2) using realtime data and place orders

```python
from zern import Trader
from credentials import user_name, password, totp_key

trader = Trader(user_name=user_name,password=password,totp_key=totp_key)

sleep(1)

token = trader.get_instrument_token_equity('infy')
insToken = token['instrument_token']

# you need to subscribe to this ticker process for live data
trader.ticker.subscribe(insToken)

# use loops or threads (preferably daemon threads) to fetch the ticker.last_msg from the ticker
# Note: 'trader.ticker.last_msg' and 'trader.ticker.last_msg_time' are the only 
#       two variables which are updated in the background
while True:
    try:
        print(trader.ticker.last_msg[str(insToken)])
    except:
        pass
    sleep(1)

```

3) placing a trade

```python
from zern import Trader
from time import sleep
from credentials import user_name, password, totp_key

trader = Trader(user_name=user_name,password=password,totp_key=totp_key)

token = trader.get_instrument_token_equity('infy')
df = trader.get_previous_data(token['instrument_token'],days=10)

# import required Types for special use cases
from zern.utils.Types import EXCHANGE,ORDER_TYPE,PRODUCT,TRANSACTION_TYPE,VARIETY,VALIDITY


# Place order
# equities need to be in PRODUCT.CNC for long or PRODUCT.MIS for intraday
# options need to be in PRODUCT.NRML for long or PRODUCT.MIS for intraday
# futures need to be in PRODUCT.NRML for long or PRODUCT.MIS for intraday
#
# refer the source code for more specific orders like limit orders, stoploss orders etc
# 
trader.place_order(token['tradingsymbol'],EXCHANGE.NSE,TRANSACTION_TYPE.BUY,1,PRODUCT.CNC)
sleep(5)
trader.place_order(token['tradingsymbol'],EXCHANGE.NSE,TRANSACTION_TYPE.SELL,1,PRODUCT.CNC)
```

**Refer the documentation for setting up options and futures trades**

## Documentation

```python
from zern import Trader
trader = Trader(user_name=YOUR_USERNAME,password=YOUR_PASSWORD,totp_key=YOUR_TOTP_KEY)
```

The `Trader` class is used to initiate the trading process and interact with the trading platform. It provides various methods to retrieve data, manage orders, and access trading information.

Check below in TOTP section if you need to get the totp key.

#### → GET YOUR INSTRUMENTS TOKENS HERE (If Required)
```python
trader.instruments #this will contain all the instrument tokens and symbols. feel free to search it as per your requirements. the helper functions also use this variable.
```

```python
trader.instrument_details #this is cache of all the instruments, can check the prices and many things of many instruments at a time without having to overload the server.
```


## Essential Methods

```python
trader.historical_data(instrument_token, start_date, end_date, interval='5minute')  #Retrieves historical data for a specific instrument within a specified time range.
```

- `instrument_token` (int): The unique identifier of the instrument.
- `start_date` (str or datetime.datetime): The start date of the historical data (format: 'YYYY-MM-DD').
- `end_date` (str or datetime.datetime): The end date of the historical data (format: 'YYYY-MM-DD').
- `interval` (str, optional): The interval for data (default: '5minute').


```python
trader.get_orders()  # Retrieves the list of orders placed by the trader.
```

```python
trader.get_positions() #Retrieves the current positions held by the trader.
```

```python
trader.get_holdings()  #Retrieves the holdings (securities owned) by the trader.
```

```python
trader.get_margins()  #Retrieves the margin details for the trader's account.
```

```python
trader.get_profile()  #Retrieves the trader's profile information.
```

```python
trader.check_app_sessions()  #Checks the active sessions for the trading application.
```
### buy and sell order placement
```python
trader.place_order(symbol, exchange, transaction_type, quantity)  #Places an order for a specific security. returns order_id 
```
required arguments:
- `symbol` (str): The symbol of the security.
- `exchange` (str or zern.utils.Types.EXCHANGE): The exchange where the security is listed (e.g., zern.utils.Types.EXCHANGE.NSE, zern.utils.Types.EXCHANGE.NFO).
- `transaction_type` (str or zern.utils.Types.TRANSACTION_TYPE): The type of transaction (e.g., zern.utils.Types.TRANSACTION_TYPE.BUY , zern.utils.Types.TRANSACTION_TYPE.SELL).
- `quantity` (int): The quantity of securities to transact.
optional keyword arguments
- `variety` (str or zern.utils.Types.VARIETY=VARIETY.REGULAR): if the order is regular, iceberg or cover order etc (e.g. VARIETY.REGULAR)
- `product`(str or zern.utils.Types.PRODUCT=PRODUCT.NRML): if order is normal or intraday (MIS) or cash n carry (CNC) (e.g. PRODUCT.NRML)
- `order_type` (str or zern.utils.Types.ORDER_TYPE=ORDER_TYPE.MARKET): if order is a type of market or limit order (e.g. ORDER_TYPE.MARKET)
- `validity` (str or zern.utils.Types.VALIDITY=VALIDITY.DAY): if order needs to be immediate (IOC) or in the day (DAY) (e.g. VALIDITY.DAY)
- `price` (str='0') : if order is limit order, it needs to be parsed into string.
- `trigger_price` (str='0') : if order is limit order, the price where it needs to trigger.
- `stoploss` (str='0') : if order needs a stoploss, the price where the stoploss is to be set.

## HELPER FUNCTIONS
These are just helper functions which only use the cached variable which is "trader.instruments". if you have further requirements, please use the variable itself to get your own data as per your need.

```python
trader.get_bnf_expiries()  #Retrieves the expiry dates for BANKNIFTY derivatives.
```

```python
trader.get_expiries(derivative_name)  #Retrieves the expiry dates for a specific derivative.
```

- `derivative_name` (str): The name of the derivative.

```python
trader.get_derivatives_list()  #Retrieves the list of available derivatives.
```

```python
trader.get_current_expiries()  #Retrieves the expiry dates for BANKNIFTY derivative.
```

```python
trader.get_strikes(derivative_name,expiry)  # retrieves the strikes for the derivative of the particular expiry
```

## EASY INSTRUMENT TOKEN RETRIEVAL FUNCTIONS

```python
trader.get_instrument_token_equity(symbol) #retrieve instrument token for a given equity symbol ex: 'INFY'
```

```python
trader.get_instrument_token_option(symbol,expiry,strike,strike_type) #retrieve instrument token for a given derivative symbol.
#trader.get_instrument_token_option('BANKNIFTY','2024-05-29','49000.0','CE')
```

```python
trader.get_instrument_token_index(symbol) #retrieve instrument token for a given index symbol ex: 'BANKNIFTY'
```

## EASY HISTORICAL DATA FUNCTIONS

```python
trader.get_previous_data(instrument_token,days=0,interval=INTERVAL.MINUTE_15) # function used to get an X number of days data from current day
```

```python
trader.get_todays_data(instrument_token)  # function used to get current day data only
```

## INBUILT DATAFRAME (ORDERED LIST)

The data from the functions is of the type (zern.utils.OrderedList.OrderedList). this is a discount version of pandas only used to view the data. if you want to convert it to Pandas DataFrame use:

```python
ins = trader.get_instrument_token_equity('infy')
ordered_list = trader.get_previous_data(ins,days=10)
pandas_df = pd.DataFrame.from_dict(ordered_list._data)
```

this ordered list can also be saved and loaded using:

```python
from zern import load_dict

ordered_list = trader.get_previous_data(ins,days=10)
ordered_list.save(path)  # save the dataframe

loaded_ordered_list = load_dict(path) #load the dataframe
```

## Live WebSocket Instructions (Important if you want to use Live Data)

when `Trader` is initatiated, a Ticker is also instantiated with it and is subscribed to BANKNIFTY and NIFTY50 at the start. 

the data is then stored in `trader.ticker.last_msg` and the time recieved is recorded in `trader.ticker.last_msg_time`

the websocket updates these two variables `trader.ticker.last_msg` and `trader.ticker.last_msg_time`, so you you can keep a while loop fetching the variables as per your requirement.

## Live Functions

```python
trader.ticker.subscribe(tokens: Union[List[int], int],mode=MODE_STRING.modeLTPC)  #subscribe the tokens as a list of instrument tokens or just an instrument token
```
- `tokens` (list , int): Expects a list of integers (instrument tokens) or just an integer (one intrument token)
- `mode` (zern.utils.Types.MODE_STRING): Expects a MODE_STRING object which is usually a string. (inspect the zern.utils.Types for more information)

```python
trader.ticker.unsubscribe(self, tokens: Union[List[int], int],mode=MODE_STRING.modeLTPC)  #unsubscribes the tokens as a list of instrument tokens or just an instrument token
```
- `tokens` (list , int): Expects a list of integers (instrument tokens) or just an integer (one intrument token)
- `mode` (zern.utils.Types.MODE_STRING): Expects a MODE_STRING object which is usually a string. (inspect the zern.utils.Types for more information)

## getting TOTP key

**_TOTP key can only be extracted from PC (mobile does not have it)_**

1) go to MyProfile  -> password and Security.
2) ![final1](https://github.com/ExBlacklight/Zern/assets/37045428/6af536ff-11c2-4a2d-b6cd-93c1a72e861e)
3) ![final2](https://github.com/ExBlacklight/Zern/assets/37045428/672c1c1c-4aa0-4fa1-b75f-45a65469ff9e)
4) copy key from there to your script and you can use it as TOTP key for automatic TOTP authentication.
5) (Optional) if you already have TOTP enabled, you need to disable TOTP and do this process again to get the key, otherwise no other way.
