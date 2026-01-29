from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ProtoException(_message.Message):
    __slots__ = ["error_message", "status_code", "code"]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STATUS_CODE_FIELD_NUMBER: _ClassVar[int]
    CODE_FIELD_NUMBER: _ClassVar[int]
    error_message: str
    status_code: int
    code: int
    def __init__(self, error_message: _Optional[str] = ..., status_code: _Optional[int] = ..., code: _Optional[int] = ...) -> None: ...
