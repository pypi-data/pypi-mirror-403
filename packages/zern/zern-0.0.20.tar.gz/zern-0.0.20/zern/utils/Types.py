from collections import namedtuple

PRODUCT = namedtuple('Product', ['NRML', 'MIS','CNC','CO'])(
    NRML='NRML',
    MIS='MIS',
    CNC='CNC',
    CO='CO')


ORDER_TYPE = namedtuple('OrderType', ['MARKET', 'LIMIT', 'SLM', 'SL'])(
    MARKET='MARKET', 
    LIMIT='LIMIT', 
    SLM='SL-M', 
    SL='SL'
)



VARIETY = namedtuple('VarietyType', ['REGULAR', 'CO', 'AMO', 'ICEBERG', 'AUCTION'])(
    REGULAR='regular', 
    CO='co', 
    AMO='amo', 
    ICEBERG='iceberg', 
    AUCTION='auction'
)


TRANSACTION_TYPE = namedtuple('TransactionType', ['BUY', 'SELL'])(
    BUY='BUY', 
    SELL='SELL'
)


VALIDITY = namedtuple('ValidityType', ['DAY', 'IOC', 'TTL'])(
    DAY='DAY', 
    IOC='IOC', 
    TTL='TTL'
)



POSITION_TYPE = namedtuple('PositionType', ['DAY', 'OVERNIGHT'])(
    DAY='day', 
    OVERNIGHT='overnight'
)


EXCHANGE = namedtuple('ExchangeType', ['NSE', 'BSE', 'NFO', 'CDS', 'BFO', 'MCX', 'BCD'])(
    NSE='NSE', 
    BSE='BSE', 
    NFO='NFO', 
    CDS='CDS', 
    BFO='BFO', 
    MCX='MCX', 
    BCD='BCD'
)


MARGIN = namedtuple('MarginType', ['EQUITY', 'COMMODITY'])(
    EQUITY='equity', 
    COMMODITY='commodity'
)


STATUS = namedtuple('StatusType', ['COMPLETE', 'REJECTED', 'CANCELLED'])(
    COMPLETE='COMPLETE', 
    REJECTED='REJECTED', 
    CANCELLED='CANCELLED'
)

SEGMENT = namedtuple('SegmentType', ['segmentNseCM','segmentNseFO','segmentNseCD','segmentBseCM','segmentBseFO','segmentBseCD','segmentMcxFO','segmentMcxSX','segmentNseIndices','segmentAuction','segmentUS','segmentNseCOM'])(
    segmentNseCM = 1,
    segmentNseFO = 2,
    segmentNseCD = 3,
    segmentBseCM = 4,
    segmentBseFO = 5,
    segmentBseCD = 6,
    segmentMcxFO = 7,
    segmentMcxSX = 8,
    segmentNseIndices = 9,
    segmentAuction = 10,
    segmentUS = 11,
    segmentNseCOM = 12
)

MODE_VALUES = namedtuple('modeType', ['modeFull', 'modeQuote', 'modeLTPC','modeLTP'])(
    modeFull = 1,
    modeQuote = 2,
    modeLTPC = 3,
    modeLTP = 4
)

MODE_STRING = namedtuple('modeType', ['modeFull', 'modeQuote', 'modeLTPC','modeLTP'])(
    modeFull = 'full',
    modeQuote = 'quote',
    modeLTPC = 'ltpc',
    modeLTP = 'ltp'
)

KEYS = namedtuple('keyOptions',['subscribe','mode','unsubscribe'])(
    subscribe='subscribe',
    mode='mode',
    unsubscribe='unsubscribe'
)

INTERVAL = namedtuple('intervalOptions',['MINUTE','MINUTE_2','MINUTE_3','MINUTE_5','MINUTE_10','MINUTE_15','MINUTE_30','HOUR','HOUR_2','HOUR_3','DAY'])(
    MINUTE='minute',
    MINUTE_2='2minute',
    MINUTE_3='3minute',
    MINUTE_5='5minute',
    MINUTE_10='10minute',
    MINUTE_15='15minute',
    MINUTE_30='30minute',
    HOUR='60minute',
    HOUR_2='2hour',
    HOUR_3='3hour',
    DAY='day'
)
