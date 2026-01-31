import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class VPNNode(_message.Message):
    __slots__ = ("id", "name", "project", "ip_addresses", "last_seen", "online")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PROJECT_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESSES_FIELD_NUMBER: _ClassVar[int]
    LAST_SEEN_FIELD_NUMBER: _ClassVar[int]
    ONLINE_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    project: str
    ip_addresses: _containers.RepeatedScalarFieldContainer[str]
    last_seen: _timestamp_pb2.Timestamp
    online: bool
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., project: _Optional[str] = ..., ip_addresses: _Optional[_Iterable[str]] = ..., last_seen: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., online: _Optional[bool] = ...) -> None: ...
