from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DateRangePbo(_message.Message):
    __slots__ = ("start_epoch_millis", "end_epoch_millis")
    START_EPOCH_MILLIS_FIELD_NUMBER: _ClassVar[int]
    END_EPOCH_MILLIS_FIELD_NUMBER: _ClassVar[int]
    start_epoch_millis: int
    end_epoch_millis: int
    def __init__(self, start_epoch_millis: _Optional[int] = ..., end_epoch_millis: _Optional[int] = ...) -> None: ...

class FieldValuePbo(_message.Message):
    __slots__ = ("string_value", "int_value", "double_value", "bool_value", "date_range")
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    DATE_RANGE_FIELD_NUMBER: _ClassVar[int]
    string_value: str
    int_value: int
    double_value: float
    bool_value: bool
    date_range: DateRangePbo
    def __init__(self, string_value: _Optional[str] = ..., int_value: _Optional[int] = ..., double_value: _Optional[float] = ..., bool_value: bool = ..., date_range: _Optional[_Union[DateRangePbo, _Mapping]] = ...) -> None: ...

class FieldValueMapPbo(_message.Message):
    __slots__ = ("fields",)
    class FieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: FieldValuePbo
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[FieldValuePbo, _Mapping]] = ...) -> None: ...
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.MessageMap[str, FieldValuePbo]
    def __init__(self, fields: _Optional[_Mapping[str, FieldValuePbo]] = ...) -> None: ...

class DataRecordPbo(_message.Message):
    __slots__ = ("data_type_name", "record_id", "fields")
    class FieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: FieldValuePbo
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[FieldValuePbo, _Mapping]] = ...) -> None: ...
    DATA_TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    RECORD_ID_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    data_type_name: str
    record_id: int
    fields: _containers.MessageMap[str, FieldValuePbo]
    def __init__(self, data_type_name: _Optional[str] = ..., record_id: _Optional[int] = ..., fields: _Optional[_Mapping[str, FieldValuePbo]] = ...) -> None: ...
