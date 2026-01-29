import order_details_pb2 as _order_details_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateOrderRequest(_message.Message):
    __slots__ = ["account_id", "symbol", "shares", "limit_price", "side", "type", "time_in_force", "route"]
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    SHARES_FIELD_NUMBER: _ClassVar[int]
    LIMIT_PRICE_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TIME_IN_FORCE_FIELD_NUMBER: _ClassVar[int]
    ROUTE_FIELD_NUMBER: _ClassVar[int]
    account_id: str
    symbol: str
    shares: float
    limit_price: float
    side: _order_details_pb2.Side
    type: _order_details_pb2.OrderType
    time_in_force: _order_details_pb2.TimeInForce
    route: _order_details_pb2.RoutingOption
    def __init__(self, account_id: _Optional[str] = ..., symbol: _Optional[str] = ..., shares: _Optional[float] = ..., limit_price: _Optional[float] = ..., side: _Optional[_Union[_order_details_pb2.Side, str]] = ..., type: _Optional[_Union[_order_details_pb2.OrderType, str]] = ..., time_in_force: _Optional[_Union[_order_details_pb2.TimeInForce, str]] = ..., route: _Optional[_Union[_order_details_pb2.RoutingOption, str]] = ...) -> None: ...
