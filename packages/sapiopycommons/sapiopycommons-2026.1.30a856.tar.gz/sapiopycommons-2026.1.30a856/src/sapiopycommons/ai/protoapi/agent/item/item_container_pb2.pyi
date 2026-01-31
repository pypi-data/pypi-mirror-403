from sapiopycommons.ai.protoapi.fielddefinitions import velox_field_def_pb2 as _velox_field_def_pb2
from sapiopycommons.ai.protoapi.fielddefinitions import fields_pb2 as _fields_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import FieldValidatorPbo as FieldValidatorPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ColorRangePbo as ColorRangePbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import BooleanDependentFieldEntryPbo as BooleanDependentFieldEntryPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import SelectionDependentFieldEntryPbo as SelectionDependentFieldEntryPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import EnumDependentFieldEntryPbo as EnumDependentFieldEntryPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ProcessDetailEntryPbo as ProcessDetailEntryPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import BooleanPropertiesPbo as BooleanPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import DatePropertiesPbo as DatePropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import DoublePropertiesPbo as DoublePropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import IntegerPropertiesPbo as IntegerPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import LongPropertiesPbo as LongPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ShortPropertiesPbo as ShortPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import SelectionPropertiesPbo as SelectionPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import StringPropertiesPbo as StringPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import SideLinkPropertiesPbo as SideLinkPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import PickListPropertiesPbo as PickListPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ParentLinkPropertiesPbo as ParentLinkPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import MultiParentPropertiesPbo as MultiParentPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import IdentifierPropertiesPbo as IdentifierPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import FileBlobPropertiesPbo as FileBlobPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import EnumPropertiesPbo as EnumPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import DateRangePropertiesPbo as DateRangePropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ChildLinkPropertiesPbo as ChildLinkPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ActionStringPropertiesPbo as ActionStringPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ActionPropertiesPbo as ActionPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import AccessionPropertiesPbo as AccessionPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import VeloxFieldDefPbo as VeloxFieldDefPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import VeloxFieldDefListPbo as VeloxFieldDefListPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import FieldTypePbo as FieldTypePbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import SortDirectionPbo as SortDirectionPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import FontSizePbo as FontSizePbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import TextDecorationPbo as TextDecorationPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import StringFormatPbo as StringFormatPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import DoubleFormatPbo as DoubleFormatPbo
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import DateRangePbo as DateRangePbo
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import FieldValuePbo as FieldValuePbo
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import FieldValueMapPbo as FieldValueMapPbo
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import DataRecordPbo as DataRecordPbo

DESCRIPTOR: _descriptor.FileDescriptor
FIELD_TYPE_UNSPECIFIED: _velox_field_def_pb2.FieldTypePbo
BOOLEAN: _velox_field_def_pb2.FieldTypePbo
DOUBLE: _velox_field_def_pb2.FieldTypePbo
ENUM: _velox_field_def_pb2.FieldTypePbo
LONG: _velox_field_def_pb2.FieldTypePbo
INTEGER: _velox_field_def_pb2.FieldTypePbo
SHORT: _velox_field_def_pb2.FieldTypePbo
STRING: _velox_field_def_pb2.FieldTypePbo
DATE: _velox_field_def_pb2.FieldTypePbo
ACTION: _velox_field_def_pb2.FieldTypePbo
SELECTION: _velox_field_def_pb2.FieldTypePbo
PARENTLINK: _velox_field_def_pb2.FieldTypePbo
IDENTIFIER: _velox_field_def_pb2.FieldTypePbo
PICKLIST: _velox_field_def_pb2.FieldTypePbo
LINK: _velox_field_def_pb2.FieldTypePbo
MULTIPARENTLINK: _velox_field_def_pb2.FieldTypePbo
CHILDLINK: _velox_field_def_pb2.FieldTypePbo
AUTO_ACCESSION: _velox_field_def_pb2.FieldTypePbo
DATE_RANGE: _velox_field_def_pb2.FieldTypePbo
SIDE_LINK: _velox_field_def_pb2.FieldTypePbo
ACTION_STRING: _velox_field_def_pb2.FieldTypePbo
FILE_BLOB: _velox_field_def_pb2.FieldTypePbo
SORT_DIRECTION_UNSPECIFIED: _velox_field_def_pb2.SortDirectionPbo
SORT_DIRECTION_ASCENDING: _velox_field_def_pb2.SortDirectionPbo
SORT_DIRECTION_DESCENDING: _velox_field_def_pb2.SortDirectionPbo
SORT_DIRECTION_NONE: _velox_field_def_pb2.SortDirectionPbo
FONT_SIZE_UNSPECIFIED: _velox_field_def_pb2.FontSizePbo
FONT_SIZE_SMALL: _velox_field_def_pb2.FontSizePbo
FONT_SIZE_MEDIUM: _velox_field_def_pb2.FontSizePbo
FONT_SIZE_LARGE: _velox_field_def_pb2.FontSizePbo
TEXT_DECORATION_UNSPECIFIED: _velox_field_def_pb2.TextDecorationPbo
TEXT_DECORATION_NONE: _velox_field_def_pb2.TextDecorationPbo
TEXT_DECORATION_UNDERLINE: _velox_field_def_pb2.TextDecorationPbo
TEXT_DECORATION_STRIKETHROUGH: _velox_field_def_pb2.TextDecorationPbo
STRING_FORMAT_UNSPECIFIED: _velox_field_def_pb2.StringFormatPbo
STRING_FORMAT_PHONE: _velox_field_def_pb2.StringFormatPbo
STRING_FORMAT_EMAIL: _velox_field_def_pb2.StringFormatPbo
DOUBLE_FORMAT_UNSPECIFIED: _velox_field_def_pb2.DoubleFormatPbo
DOUBLE_FORMAT_CURRENCY: _velox_field_def_pb2.DoubleFormatPbo
DOUBLE_FORMAT_PERCENTAGE: _velox_field_def_pb2.DoubleFormatPbo

class DataTypePbo(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BINARY: _ClassVar[DataTypePbo]
    JSON: _ClassVar[DataTypePbo]
    CSV: _ClassVar[DataTypePbo]
    TEXT: _ClassVar[DataTypePbo]
    IMAGE: _ClassVar[DataTypePbo]
    DATA_RECORD: _ClassVar[DataTypePbo]
BINARY: DataTypePbo
JSON: DataTypePbo
CSV: DataTypePbo
TEXT: DataTypePbo
IMAGE: DataTypePbo
DATA_RECORD: DataTypePbo

class ContentTypePbo(_message.Message):
    __slots__ = ("name", "extensions", "display_name")
    NAME_FIELD_NUMBER: _ClassVar[int]
    EXTENSIONS_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    extensions: _containers.RepeatedScalarFieldContainer[str]
    display_name: str
    def __init__(self, name: _Optional[str] = ..., extensions: _Optional[_Iterable[str]] = ..., display_name: _Optional[str] = ...) -> None: ...

class StepCsvHeaderRowPbo(_message.Message):
    __slots__ = ("cells",)
    CELLS_FIELD_NUMBER: _ClassVar[int]
    cells: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, cells: _Optional[_Iterable[str]] = ...) -> None: ...

class StepCsvRowPbo(_message.Message):
    __slots__ = ("cells",)
    CELLS_FIELD_NUMBER: _ClassVar[int]
    cells: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, cells: _Optional[_Iterable[str]] = ...) -> None: ...

class StepCsvContainerPbo(_message.Message):
    __slots__ = ("header", "items")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    header: StepCsvHeaderRowPbo
    items: _containers.RepeatedCompositeFieldContainer[StepCsvRowPbo]
    def __init__(self, header: _Optional[_Union[StepCsvHeaderRowPbo, _Mapping]] = ..., items: _Optional[_Iterable[_Union[StepCsvRowPbo, _Mapping]]] = ...) -> None: ...

class StepJsonContainerPbo(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, items: _Optional[_Iterable[str]] = ...) -> None: ...

class StepTextContainerPbo(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, items: _Optional[_Iterable[str]] = ...) -> None: ...

class StepBinaryContainerPbo(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, items: _Optional[_Iterable[bytes]] = ...) -> None: ...

class StepImageContainerPbo(_message.Message):
    __slots__ = ("image_format", "items")
    IMAGE_FORMAT_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    image_format: str
    items: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, image_format: _Optional[str] = ..., items: _Optional[_Iterable[bytes]] = ...) -> None: ...

class StepDataRecordContainerPbo(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[_fields_pb2.DataRecordPbo]
    def __init__(self, items: _Optional[_Iterable[_Union[_fields_pb2.DataRecordPbo, _Mapping]]] = ...) -> None: ...

class StepItemContainerPbo(_message.Message):
    __slots__ = ("content_type", "container_name", "binary_container", "csv_container", "json_container", "text_container", "data_record_container")
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONTAINER_NAME_FIELD_NUMBER: _ClassVar[int]
    BINARY_CONTAINER_FIELD_NUMBER: _ClassVar[int]
    CSV_CONTAINER_FIELD_NUMBER: _ClassVar[int]
    JSON_CONTAINER_FIELD_NUMBER: _ClassVar[int]
    TEXT_CONTAINER_FIELD_NUMBER: _ClassVar[int]
    DATA_RECORD_CONTAINER_FIELD_NUMBER: _ClassVar[int]
    content_type: ContentTypePbo
    container_name: str
    binary_container: StepBinaryContainerPbo
    csv_container: StepCsvContainerPbo
    json_container: StepJsonContainerPbo
    text_container: StepTextContainerPbo
    data_record_container: StepDataRecordContainerPbo
    def __init__(self, content_type: _Optional[_Union[ContentTypePbo, _Mapping]] = ..., container_name: _Optional[str] = ..., binary_container: _Optional[_Union[StepBinaryContainerPbo, _Mapping]] = ..., csv_container: _Optional[_Union[StepCsvContainerPbo, _Mapping]] = ..., json_container: _Optional[_Union[StepJsonContainerPbo, _Mapping]] = ..., text_container: _Optional[_Union[StepTextContainerPbo, _Mapping]] = ..., data_record_container: _Optional[_Union[StepDataRecordContainerPbo, _Mapping]] = ...) -> None: ...
