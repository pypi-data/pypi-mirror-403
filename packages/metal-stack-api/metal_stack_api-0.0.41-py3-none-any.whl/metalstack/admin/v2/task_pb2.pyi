import datetime

from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from metalstack.api.v2 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TaskState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TASK_STATE_UNSPECIFIED: _ClassVar[TaskState]
    TASK_STATE_ACTIVE: _ClassVar[TaskState]
    TASK_STATE_PENDING: _ClassVar[TaskState]
    TASK_STATE_SCHEDULED: _ClassVar[TaskState]
    TASK_STATE_RETRY: _ClassVar[TaskState]
    TASK_STATE_ARCHIVED: _ClassVar[TaskState]
    TASK_STATE_COMPLETED: _ClassVar[TaskState]
    TASK_STATE_AGGREGATING: _ClassVar[TaskState]
TASK_STATE_UNSPECIFIED: TaskState
TASK_STATE_ACTIVE: TaskState
TASK_STATE_PENDING: TaskState
TASK_STATE_SCHEDULED: TaskState
TASK_STATE_RETRY: TaskState
TASK_STATE_ARCHIVED: TaskState
TASK_STATE_COMPLETED: TaskState
TASK_STATE_AGGREGATING: TaskState

class TaskServiceGetRequest(_message.Message):
    __slots__ = ("task_id", "queue")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    QUEUE_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    queue: str
    def __init__(self, task_id: _Optional[str] = ..., queue: _Optional[str] = ...) -> None: ...

class TaskServiceGetResponse(_message.Message):
    __slots__ = ("task",)
    TASK_FIELD_NUMBER: _ClassVar[int]
    task: TaskInfo
    def __init__(self, task: _Optional[_Union[TaskInfo, _Mapping]] = ...) -> None: ...

class TaskServiceDeleteRequest(_message.Message):
    __slots__ = ("task_id", "queue")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    QUEUE_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    queue: str
    def __init__(self, task_id: _Optional[str] = ..., queue: _Optional[str] = ...) -> None: ...

class TaskServiceDeleteResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TaskServiceQueuesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TaskServiceQueuesResponse(_message.Message):
    __slots__ = ("queues",)
    QUEUES_FIELD_NUMBER: _ClassVar[int]
    queues: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, queues: _Optional[_Iterable[str]] = ...) -> None: ...

class TaskServiceListRequest(_message.Message):
    __slots__ = ("queue", "count", "page")
    QUEUE_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    queue: str
    count: int
    page: int
    def __init__(self, queue: _Optional[str] = ..., count: _Optional[int] = ..., page: _Optional[int] = ...) -> None: ...

class TaskServiceListResponse(_message.Message):
    __slots__ = ("tasks",)
    TASKS_FIELD_NUMBER: _ClassVar[int]
    tasks: _containers.RepeatedCompositeFieldContainer[TaskInfo]
    def __init__(self, tasks: _Optional[_Iterable[_Union[TaskInfo, _Mapping]]] = ...) -> None: ...

class TaskInfo(_message.Message):
    __slots__ = ("id", "queue", "type", "payload", "state", "max_retry", "retried", "last_error", "last_failed_at", "timeout", "deadline", "group", "next_process_at", "is_orphaned", "retention", "completed_at", "result")
    ID_FIELD_NUMBER: _ClassVar[int]
    QUEUE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    MAX_RETRY_FIELD_NUMBER: _ClassVar[int]
    RETRIED_FIELD_NUMBER: _ClassVar[int]
    LAST_ERROR_FIELD_NUMBER: _ClassVar[int]
    LAST_FAILED_AT_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    NEXT_PROCESS_AT_FIELD_NUMBER: _ClassVar[int]
    IS_ORPHANED_FIELD_NUMBER: _ClassVar[int]
    RETENTION_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_AT_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    id: str
    queue: str
    type: str
    payload: bytes
    state: TaskState
    max_retry: int
    retried: int
    last_error: str
    last_failed_at: _timestamp_pb2.Timestamp
    timeout: _duration_pb2.Duration
    deadline: _timestamp_pb2.Timestamp
    group: str
    next_process_at: _timestamp_pb2.Timestamp
    is_orphaned: bool
    retention: _duration_pb2.Duration
    completed_at: _timestamp_pb2.Timestamp
    result: bytes
    def __init__(self, id: _Optional[str] = ..., queue: _Optional[str] = ..., type: _Optional[str] = ..., payload: _Optional[bytes] = ..., state: _Optional[_Union[TaskState, str]] = ..., max_retry: _Optional[int] = ..., retried: _Optional[int] = ..., last_error: _Optional[str] = ..., last_failed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., timeout: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., deadline: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., group: _Optional[str] = ..., next_process_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., is_orphaned: _Optional[bool] = ..., retention: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., completed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., result: _Optional[bytes] = ...) -> None: ...
