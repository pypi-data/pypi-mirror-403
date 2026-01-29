from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class OrderResponse(_message.Message):
    __slots__ = ["success", "status", "id"]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    status: str
    id: str
    def __init__(self, success: bool = ..., status: _Optional[str] = ..., id: _Optional[str] = ...) -> None: ...
