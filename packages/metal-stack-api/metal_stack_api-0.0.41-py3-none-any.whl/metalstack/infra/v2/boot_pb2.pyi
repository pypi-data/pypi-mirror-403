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

class BootServiceDhcpRequest(_message.Message):
    __slots__ = ("uuid", "partition")
    UUID_FIELD_NUMBER: _ClassVar[int]
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    partition: str
    def __init__(self, uuid: _Optional[str] = ..., partition: _Optional[str] = ...) -> None: ...

class BootServiceDhcpResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class BootServiceBootRequest(_message.Message):
    __slots__ = ("mac", "partition")
    MAC_FIELD_NUMBER: _ClassVar[int]
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    mac: str
    partition: str
    def __init__(self, mac: _Optional[str] = ..., partition: _Optional[str] = ...) -> None: ...

class BootServiceBootResponse(_message.Message):
    __slots__ = ("kernel", "init_ram_disks", "cmdline")
    KERNEL_FIELD_NUMBER: _ClassVar[int]
    INIT_RAM_DISKS_FIELD_NUMBER: _ClassVar[int]
    CMDLINE_FIELD_NUMBER: _ClassVar[int]
    kernel: str
    init_ram_disks: _containers.RepeatedScalarFieldContainer[str]
    cmdline: str
    def __init__(self, kernel: _Optional[str] = ..., init_ram_disks: _Optional[_Iterable[str]] = ..., cmdline: _Optional[str] = ...) -> None: ...

class BootServiceRegisterRequest(_message.Message):
    __slots__ = ("uuid", "hardware", "bios", "bmc", "fru", "tags", "metal_hammer_version", "partition")
    UUID_FIELD_NUMBER: _ClassVar[int]
    HARDWARE_FIELD_NUMBER: _ClassVar[int]
    BIOS_FIELD_NUMBER: _ClassVar[int]
    BMC_FIELD_NUMBER: _ClassVar[int]
    FRU_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    METAL_HAMMER_VERSION_FIELD_NUMBER: _ClassVar[int]
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    hardware: _machine_pb2.MachineHardware
    bios: _machine_pb2.MachineBios
    bmc: _machine_pb2.MachineBMC
    fru: _machine_pb2.MachineFRU
    tags: _containers.RepeatedScalarFieldContainer[str]
    metal_hammer_version: str
    partition: str
    def __init__(self, uuid: _Optional[str] = ..., hardware: _Optional[_Union[_machine_pb2.MachineHardware, _Mapping]] = ..., bios: _Optional[_Union[_machine_pb2.MachineBios, _Mapping]] = ..., bmc: _Optional[_Union[_machine_pb2.MachineBMC, _Mapping]] = ..., fru: _Optional[_Union[_machine_pb2.MachineFRU, _Mapping]] = ..., tags: _Optional[_Iterable[str]] = ..., metal_hammer_version: _Optional[str] = ..., partition: _Optional[str] = ...) -> None: ...

class BootServiceRegisterResponse(_message.Message):
    __slots__ = ("uuid", "size", "partition")
    UUID_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    size: str
    partition: str
    def __init__(self, uuid: _Optional[str] = ..., size: _Optional[str] = ..., partition: _Optional[str] = ...) -> None: ...

class BootServiceWaitRequest(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class BootServiceWaitResponse(_message.Message):
    __slots__ = ("allocation",)
    ALLOCATION_FIELD_NUMBER: _ClassVar[int]
    allocation: _machine_pb2.MachineAllocation
    def __init__(self, allocation: _Optional[_Union[_machine_pb2.MachineAllocation, _Mapping]] = ...) -> None: ...

class BootServiceInstallationSucceededRequest(_message.Message):
    __slots__ = ("uuid", "console_password")
    UUID_FIELD_NUMBER: _ClassVar[int]
    CONSOLE_PASSWORD_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    console_password: str
    def __init__(self, uuid: _Optional[str] = ..., console_password: _Optional[str] = ...) -> None: ...

class BootServiceInstallationSucceededResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class BootServiceSuperUserPasswordRequest(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class BootServiceSuperUserPasswordResponse(_message.Message):
    __slots__ = ("feature_disabled", "super_user_password")
    FEATURE_DISABLED_FIELD_NUMBER: _ClassVar[int]
    SUPER_USER_PASSWORD_FIELD_NUMBER: _ClassVar[int]
    feature_disabled: bool
    super_user_password: str
    def __init__(self, feature_disabled: _Optional[bool] = ..., super_user_password: _Optional[str] = ...) -> None: ...
