from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class CancelOrderRequest(_message.Message):
    __slots__ = ["account_id", "order_id"]
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    account_id: str
    order_id: str
    def __init__(self, account_id: _Optional[str] = ..., order_id: _Optional[str] = ...) -> None: ...
