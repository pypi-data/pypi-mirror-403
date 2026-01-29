from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AccountType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    CASH: _ClassVar[AccountType]
    IRA_TRADITIONAL: _ClassVar[AccountType]
    IRA_ROTH: _ClassVar[AccountType]
CASH: AccountType
IRA_TRADITIONAL: AccountType
IRA_ROTH: AccountType

class Account(_message.Message):
    __slots__ = ["id", "name", "account_type"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_TYPE_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    account_type: AccountType
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., account_type: _Optional[_Union[AccountType, str]] = ...) -> None: ...

class AccountsResponse(_message.Message):
    __slots__ = ["accounts"]
    ACCOUNTS_FIELD_NUMBER: _ClassVar[int]
    accounts: _containers.RepeatedCompositeFieldContainer[Account]
    def __init__(self, accounts: _Optional[_Iterable[_Union[Account, _Mapping]]] = ...) -> None: ...
