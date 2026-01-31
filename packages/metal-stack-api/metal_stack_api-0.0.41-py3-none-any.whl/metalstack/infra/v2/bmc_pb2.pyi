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

class UpdateBMCInfoRequest(_message.Message):
    __slots__ = ("partition", "bmc_reports")
    class BmcReportsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _machine_pb2.MachineBMCReport
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_machine_pb2.MachineBMCReport, _Mapping]] = ...) -> None: ...
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    BMC_REPORTS_FIELD_NUMBER: _ClassVar[int]
    partition: str
    bmc_reports: _containers.MessageMap[str, _machine_pb2.MachineBMCReport]
    def __init__(self, partition: _Optional[str] = ..., bmc_reports: _Optional[_Mapping[str, _machine_pb2.MachineBMCReport]] = ...) -> None: ...

class UpdateBMCInfoResponse(_message.Message):
    __slots__ = ("updated_machines", "created_machines")
    UPDATED_MACHINES_FIELD_NUMBER: _ClassVar[int]
    CREATED_MACHINES_FIELD_NUMBER: _ClassVar[int]
    updated_machines: _containers.RepeatedScalarFieldContainer[str]
    created_machines: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, updated_machines: _Optional[_Iterable[str]] = ..., created_machines: _Optional[_Iterable[str]] = ...) -> None: ...

class WaitForBMCCommandRequest(_message.Message):
    __slots__ = ("partition",)
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    partition: str
    def __init__(self, partition: _Optional[str] = ...) -> None: ...

class WaitForBMCCommandResponse(_message.Message):
    __slots__ = ("uuid", "bmc_command", "machine_bmc", "command_id")
    UUID_FIELD_NUMBER: _ClassVar[int]
    BMC_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MACHINE_BMC_FIELD_NUMBER: _ClassVar[int]
    COMMAND_ID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    bmc_command: _machine_pb2.MachineBMCCommand
    machine_bmc: _machine_pb2.MachineBMC
    command_id: str
    def __init__(self, uuid: _Optional[str] = ..., bmc_command: _Optional[_Union[_machine_pb2.MachineBMCCommand, str]] = ..., machine_bmc: _Optional[_Union[_machine_pb2.MachineBMC, _Mapping]] = ..., command_id: _Optional[str] = ...) -> None: ...

class BMCCommandDoneRequest(_message.Message):
    __slots__ = ("command_id", "error")
    COMMAND_ID_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    command_id: str
    error: str
    def __init__(self, command_id: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class BMCCommandDoneResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
