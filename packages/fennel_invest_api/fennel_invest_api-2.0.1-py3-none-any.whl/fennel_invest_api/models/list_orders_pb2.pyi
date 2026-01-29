from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ListOrdersRequest(_message.Message):
    __slots__ = ["account_id", "since_date"]
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    SINCE_DATE_FIELD_NUMBER: _ClassVar[int]
    account_id: str
    since_date: _timestamp_pb2.Timestamp
    def __init__(self, account_id: _Optional[str] = ..., since_date: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class OrderFill(_message.Message):
    __slots__ = ["side", "settlement_date", "quantity", "price"]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    SETTLEMENT_DATE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    side: str
    settlement_date: _timestamp_pb2.Timestamp
    quantity: float
    price: float
    def __init__(self, side: _Optional[str] = ..., settlement_date: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., quantity: _Optional[float] = ..., price: _Optional[float] = ...) -> None: ...

class Order(_message.Message):
    __slots__ = ["id", "ticker", "status", "created", "fills", "average_fill_price"]
    ID_FIELD_NUMBER: _ClassVar[int]
    TICKER_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_FIELD_NUMBER: _ClassVar[int]
    FILLS_FIELD_NUMBER: _ClassVar[int]
    AVERAGE_FILL_PRICE_FIELD_NUMBER: _ClassVar[int]
    id: str
    ticker: str
    status: str
    created: _timestamp_pb2.Timestamp
    fills: _containers.RepeatedCompositeFieldContainer[OrderFill]
    average_fill_price: float
    def __init__(self, id: _Optional[str] = ..., ticker: _Optional[str] = ..., status: _Optional[str] = ..., created: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., fills: _Optional[_Iterable[_Union[OrderFill, _Mapping]]] = ..., average_fill_price: _Optional[float] = ...) -> None: ...

class ListOrdersResponse(_message.Message):
    __slots__ = ["orders", "message"]
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    orders: _containers.RepeatedCompositeFieldContainer[Order]
    message: str
    def __init__(self, orders: _Optional[_Iterable[_Union[Order, _Mapping]]] = ..., message: _Optional[str] = ...) -> None: ...
