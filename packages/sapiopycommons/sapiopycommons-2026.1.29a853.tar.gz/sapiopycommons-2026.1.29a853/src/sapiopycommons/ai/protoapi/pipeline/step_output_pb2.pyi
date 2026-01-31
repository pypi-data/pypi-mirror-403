from sapiopycommons.ai.protoapi.fielddefinitions import fields_pb2 as _fields_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import DateRangePbo as DateRangePbo
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import FieldValuePbo as FieldValuePbo
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import FieldValueMapPbo as FieldValueMapPbo
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import DataRecordPbo as DataRecordPbo

DESCRIPTOR: _descriptor.FileDescriptor

class StepJsonSingletonItemPbo(_message.Message):
    __slots__ = ("item",)
    ITEM_FIELD_NUMBER: _ClassVar[int]
    item: str
    def __init__(self, item: _Optional[str] = ...) -> None: ...

class StepTextSingletonItemPbo(_message.Message):
    __slots__ = ("item",)
    ITEM_FIELD_NUMBER: _ClassVar[int]
    item: str
    def __init__(self, item: _Optional[str] = ...) -> None: ...

class StepCsvSingletonItemPbo(_message.Message):
    __slots__ = ("cells",)
    CELLS_FIELD_NUMBER: _ClassVar[int]
    cells: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, cells: _Optional[_Iterable[str]] = ...) -> None: ...

class StepBinarySingletonItemPbo(_message.Message):
    __slots__ = ("item",)
    ITEM_FIELD_NUMBER: _ClassVar[int]
    item: bytes
    def __init__(self, item: _Optional[bytes] = ...) -> None: ...

class StepDataRecordSingletonItemPbo(_message.Message):
    __slots__ = ("item",)
    ITEM_FIELD_NUMBER: _ClassVar[int]
    item: _fields_pb2.DataRecordPbo
    def __init__(self, item: _Optional[_Union[_fields_pb2.DataRecordPbo, _Mapping]] = ...) -> None: ...

class StepSingletonItemPbo(_message.Message):
    __slots__ = ("json_singleton", "text_singleton", "csv_singleton", "binary_singleton", "data_record_singleton")
    JSON_SINGLETON_FIELD_NUMBER: _ClassVar[int]
    TEXT_SINGLETON_FIELD_NUMBER: _ClassVar[int]
    CSV_SINGLETON_FIELD_NUMBER: _ClassVar[int]
    BINARY_SINGLETON_FIELD_NUMBER: _ClassVar[int]
    DATA_RECORD_SINGLETON_FIELD_NUMBER: _ClassVar[int]
    json_singleton: StepJsonSingletonItemPbo
    text_singleton: StepTextSingletonItemPbo
    csv_singleton: StepCsvSingletonItemPbo
    binary_singleton: StepBinarySingletonItemPbo
    data_record_singleton: StepDataRecordSingletonItemPbo
    def __init__(self, json_singleton: _Optional[_Union[StepJsonSingletonItemPbo, _Mapping]] = ..., text_singleton: _Optional[_Union[StepTextSingletonItemPbo, _Mapping]] = ..., csv_singleton: _Optional[_Union[StepCsvSingletonItemPbo, _Mapping]] = ..., binary_singleton: _Optional[_Union[StepBinarySingletonItemPbo, _Mapping]] = ..., data_record_singleton: _Optional[_Union[StepDataRecordSingletonItemPbo, _Mapping]] = ...) -> None: ...
