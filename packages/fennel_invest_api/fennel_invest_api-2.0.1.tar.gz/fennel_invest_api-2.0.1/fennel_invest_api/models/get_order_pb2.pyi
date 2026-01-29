from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class GetOrderRequest(_message.Message):
    __slots__ = ["order_id"]
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    def __init__(self, order_id: _Optional[str] = ...) -> None: ...
