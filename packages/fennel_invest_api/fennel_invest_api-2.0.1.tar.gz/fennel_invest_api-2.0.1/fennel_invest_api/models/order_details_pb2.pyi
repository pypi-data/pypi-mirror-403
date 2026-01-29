from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Side(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    SIDE_UNSPECIFIED: _ClassVar[Side]
    BUY: _ClassVar[Side]
    SELL: _ClassVar[Side]

class OrderType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    ORDER_UNSPECIFIED: _ClassVar[OrderType]
    MARKET: _ClassVar[OrderType]
    LIMIT: _ClassVar[OrderType]

class TimeInForce(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    TIME_UNSPECIFIED: _ClassVar[TimeInForce]
    DAY: _ClassVar[TimeInForce]

class RoutingOption(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    ROUTING_UNSPECIFIED: _ClassVar[RoutingOption]
    EXCHANGE: _ClassVar[RoutingOption]
    EXCHANGE_ATS: _ClassVar[RoutingOption]
    EXCHANGE_ATS_SDP: _ClassVar[RoutingOption]
    QUIK: _ClassVar[RoutingOption]
SIDE_UNSPECIFIED: Side
BUY: Side
SELL: Side
ORDER_UNSPECIFIED: OrderType
MARKET: OrderType
LIMIT: OrderType
TIME_UNSPECIFIED: TimeInForce
DAY: TimeInForce
ROUTING_UNSPECIFIED: RoutingOption
EXCHANGE: RoutingOption
EXCHANGE_ATS: RoutingOption
EXCHANGE_ATS_SDP: RoutingOption
QUIK: RoutingOption

class OrderDetails(_message.Message):
    __slots__ = ["symbol", "shares", "limit_price", "side", "type", "time_in_force", "route"]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    SHARES_FIELD_NUMBER: _ClassVar[int]
    LIMIT_PRICE_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TIME_IN_FORCE_FIELD_NUMBER: _ClassVar[int]
    ROUTE_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    shares: float
    limit_price: float
    side: Side
    type: OrderType
    time_in_force: TimeInForce
    route: RoutingOption
    def __init__(self, symbol: _Optional[str] = ..., shares: _Optional[float] = ..., limit_price: _Optional[float] = ..., side: _Optional[_Union[Side, str]] = ..., type: _Optional[_Union[OrderType, str]] = ..., time_in_force: _Optional[_Union[TimeInForce, str]] = ..., route: _Optional[_Union[RoutingOption, str]] = ...) -> None: ...
