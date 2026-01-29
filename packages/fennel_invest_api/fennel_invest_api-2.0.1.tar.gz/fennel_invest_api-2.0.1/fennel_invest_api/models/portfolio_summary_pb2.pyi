from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PortfolioSummaryResponse(_message.Message):
    __slots__ = ["portfolio_value", "buying_power", "cash_available"]
    PORTFOLIO_VALUE_FIELD_NUMBER: _ClassVar[int]
    BUYING_POWER_FIELD_NUMBER: _ClassVar[int]
    CASH_AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    portfolio_value: float
    buying_power: float
    cash_available: float
    def __init__(self, portfolio_value: _Optional[float] = ..., buying_power: _Optional[float] = ..., cash_available: _Optional[float] = ...) -> None: ...
