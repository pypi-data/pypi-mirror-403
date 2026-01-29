from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Position(_message.Message):
    __slots__ = ["symbol", "shares", "value"]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    SHARES_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    shares: float
    value: float
    def __init__(self, symbol: _Optional[str] = ..., shares: _Optional[float] = ..., value: _Optional[float] = ...) -> None: ...

class PositionsResponse(_message.Message):
    __slots__ = ["positions"]
    POSITIONS_FIELD_NUMBER: _ClassVar[int]
    positions: _containers.RepeatedCompositeFieldContainer[Position]
    def __init__(self, positions: _Optional[_Iterable[_Union[Position, _Mapping]]] = ...) -> None: ...
