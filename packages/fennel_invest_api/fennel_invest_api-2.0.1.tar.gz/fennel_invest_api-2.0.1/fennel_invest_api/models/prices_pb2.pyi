from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MultiPriceRequest(_message.Message):
    __slots__ = ["symbols"]
    SYMBOLS_FIELD_NUMBER: _ClassVar[int]
    symbols: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, symbols: _Optional[_Iterable[str]] = ...) -> None: ...

class PriceResponse(_message.Message):
    __slots__ = ["symbol", "price"]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    price: float
    def __init__(self, symbol: _Optional[str] = ..., price: _Optional[float] = ...) -> None: ...

class MultiPriceResponse(_message.Message):
    __slots__ = ["prices"]
    PRICES_FIELD_NUMBER: _ClassVar[int]
    prices: _containers.RepeatedCompositeFieldContainer[PriceResponse]
    def __init__(self, prices: _Optional[_Iterable[_Union[PriceResponse, _Mapping]]] = ...) -> None: ...
