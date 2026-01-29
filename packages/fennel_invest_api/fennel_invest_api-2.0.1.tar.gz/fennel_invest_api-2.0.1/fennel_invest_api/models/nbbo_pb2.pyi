from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class NbboRequest(_message.Message):
    __slots__ = ["symbol"]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    def __init__(self, symbol: _Optional[str] = ...) -> None: ...

class NbboResponse(_message.Message):
    __slots__ = ["ticker", "exchange_code", "bid_price", "num_bid_shares", "ask_price", "num_ask_shares", "last_sale_price", "last_sale_shares"]
    TICKER_FIELD_NUMBER: _ClassVar[int]
    EXCHANGE_CODE_FIELD_NUMBER: _ClassVar[int]
    BID_PRICE_FIELD_NUMBER: _ClassVar[int]
    NUM_BID_SHARES_FIELD_NUMBER: _ClassVar[int]
    ASK_PRICE_FIELD_NUMBER: _ClassVar[int]
    NUM_ASK_SHARES_FIELD_NUMBER: _ClassVar[int]
    LAST_SALE_PRICE_FIELD_NUMBER: _ClassVar[int]
    LAST_SALE_SHARES_FIELD_NUMBER: _ClassVar[int]
    ticker: str
    exchange_code: str
    bid_price: float
    num_bid_shares: float
    ask_price: float
    num_ask_shares: float
    last_sale_price: float
    last_sale_shares: float
    def __init__(self, ticker: _Optional[str] = ..., exchange_code: _Optional[str] = ..., bid_price: _Optional[float] = ..., num_bid_shares: _Optional[float] = ..., ask_price: _Optional[float] = ..., num_ask_shares: _Optional[float] = ..., last_sale_price: _Optional[float] = ..., last_sale_shares: _Optional[float] = ...) -> None: ...
