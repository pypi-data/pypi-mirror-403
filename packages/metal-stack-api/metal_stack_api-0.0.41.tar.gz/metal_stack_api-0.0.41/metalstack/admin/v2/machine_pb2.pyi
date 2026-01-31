from buf.validate import validate_pb2 as _validate_pb2
from metalstack.api.v2 import common_pb2 as _common_pb2
from metalstack.api.v2 import machine_pb2 as _machine_pb2
from metalstack.api.v2 import predefined_rules_pb2 as _predefined_rules_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MachineServiceGetRequest(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class MachineServiceGetResponse(_message.Message):
    __slots__ = ("machine",)
    MACHINE_FIELD_NUMBER: _ClassVar[int]
    machine: _machine_pb2.Machine
    def __init__(self, machine: _Optional[_Union[_machine_pb2.Machine, _Mapping]] = ...) -> None: ...

class MachineServiceListRequest(_message.Message):
    __slots__ = ("query", "partition")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    query: _machine_pb2.MachineQuery
    partition: str
    def __init__(self, query: _Optional[_Union[_machine_pb2.MachineQuery, _Mapping]] = ..., partition: _Optional[str] = ...) -> None: ...

class MachineServiceListResponse(_message.Message):
    __slots__ = ("machines",)
    MACHINES_FIELD_NUMBER: _ClassVar[int]
    machines: _containers.RepeatedCompositeFieldContainer[_machine_pb2.Machine]
    def __init__(self, machines: _Optional[_Iterable[_Union[_machine_pb2.Machine, _Mapping]]] = ...) -> None: ...

class MachineServiceBMCCommandRequest(_message.Message):
    __slots__ = ("uuid", "command")
    UUID_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    command: _machine_pb2.MachineBMCCommand
    def __init__(self, uuid: _Optional[str] = ..., command: _Optional[_Union[_machine_pb2.MachineBMCCommand, str]] = ...) -> None: ...

class MachineServiceBMCCommandResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MachineServiceGetBMCRequest(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class MachineServiceGetBMCResponse(_message.Message):
    __slots__ = ("uuid", "bmc")
    UUID_FIELD_NUMBER: _ClassVar[int]
    BMC_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    bmc: _machine_pb2.MachineBMCReport
    def __init__(self, uuid: _Optional[str] = ..., bmc: _Optional[_Union[_machine_pb2.MachineBMCReport, _Mapping]] = ...) -> None: ...

class MachineServiceListBMCRequest(_message.Message):
    __slots__ = ("query",)
    QUERY_FIELD_NUMBER: _ClassVar[int]
    query: _machine_pb2.MachineBMCQuery
    def __init__(self, query: _Optional[_Union[_machine_pb2.MachineBMCQuery, _Mapping]] = ...) -> None: ...

class MachineServiceListBMCResponse(_message.Message):
    __slots__ = ("bmc_reports",)
    class BmcReportsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _machine_pb2.MachineBMCReport
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_machine_pb2.MachineBMCReport, _Mapping]] = ...) -> None: ...
    BMC_REPORTS_FIELD_NUMBER: _ClassVar[int]
    bmc_reports: _containers.MessageMap[str, _machine_pb2.MachineBMCReport]
    def __init__(self, bmc_reports: _Optional[_Mapping[str, _machine_pb2.MachineBMCReport]] = ...) -> None: ...

class MachineServiceConsolePasswordRequest(_message.Message):
    __slots__ = ("uuid", "reason")
    UUID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    reason: str
    def __init__(self, uuid: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class MachineServiceConsolePasswordResponse(_message.Message):
    __slots__ = ("uuid", "password")
    UUID_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    password: str
    def __init__(self, uuid: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...
