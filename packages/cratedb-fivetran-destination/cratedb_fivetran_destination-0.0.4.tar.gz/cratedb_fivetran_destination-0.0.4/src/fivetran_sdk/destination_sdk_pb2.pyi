import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Encryption(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[Encryption]
    AES: _ClassVar[Encryption]

class BatchFileFormat(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CSV: _ClassVar[BatchFileFormat]
    PARQUET: _ClassVar[BatchFileFormat]

class Compression(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OFF: _ClassVar[Compression]
    ZSTD: _ClassVar[Compression]
    GZIP: _ClassVar[Compression]

class TableSyncModeMigrationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SOFT_DELETE_TO_LIVE: _ClassVar[TableSyncModeMigrationType]
    SOFT_DELETE_TO_HISTORY: _ClassVar[TableSyncModeMigrationType]
    HISTORY_TO_SOFT_DELETE: _ClassVar[TableSyncModeMigrationType]
    HISTORY_TO_LIVE: _ClassVar[TableSyncModeMigrationType]
    LIVE_TO_SOFT_DELETE: _ClassVar[TableSyncModeMigrationType]
    LIVE_TO_HISTORY: _ClassVar[TableSyncModeMigrationType]
NONE: Encryption
AES: Encryption
CSV: BatchFileFormat
PARQUET: BatchFileFormat
OFF: Compression
ZSTD: Compression
GZIP: Compression
SOFT_DELETE_TO_LIVE: TableSyncModeMigrationType
SOFT_DELETE_TO_HISTORY: TableSyncModeMigrationType
HISTORY_TO_SOFT_DELETE: TableSyncModeMigrationType
HISTORY_TO_LIVE: TableSyncModeMigrationType
LIVE_TO_SOFT_DELETE: TableSyncModeMigrationType
LIVE_TO_HISTORY: TableSyncModeMigrationType

class CapabilitiesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CapabilitiesResponse(_message.Message):
    __slots__ = ("batch_file_format",)
    BATCH_FILE_FORMAT_FIELD_NUMBER: _ClassVar[int]
    batch_file_format: BatchFileFormat
    def __init__(self, batch_file_format: _Optional[_Union[BatchFileFormat, str]] = ...) -> None: ...

class DescribeTableRequest(_message.Message):
    __slots__ = ("configuration", "schema_name", "table_name")
    class ConfigurationEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    configuration: _containers.ScalarMap[str, str]
    schema_name: str
    table_name: str
    def __init__(self, configuration: _Optional[_Mapping[str, str]] = ..., schema_name: _Optional[str] = ..., table_name: _Optional[str] = ...) -> None: ...

class DescribeTableResponse(_message.Message):
    __slots__ = ("not_found", "table", "warning", "task")
    NOT_FOUND_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    WARNING_FIELD_NUMBER: _ClassVar[int]
    TASK_FIELD_NUMBER: _ClassVar[int]
    not_found: bool
    table: _common_pb2.Table
    warning: _common_pb2.Warning
    task: _common_pb2.Task
    def __init__(self, not_found: bool = ..., table: _Optional[_Union[_common_pb2.Table, _Mapping]] = ..., warning: _Optional[_Union[_common_pb2.Warning, _Mapping]] = ..., task: _Optional[_Union[_common_pb2.Task, _Mapping]] = ...) -> None: ...

class CreateTableRequest(_message.Message):
    __slots__ = ("configuration", "schema_name", "table")
    class ConfigurationEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    configuration: _containers.ScalarMap[str, str]
    schema_name: str
    table: _common_pb2.Table
    def __init__(self, configuration: _Optional[_Mapping[str, str]] = ..., schema_name: _Optional[str] = ..., table: _Optional[_Union[_common_pb2.Table, _Mapping]] = ...) -> None: ...

class CreateTableResponse(_message.Message):
    __slots__ = ("success", "warning", "task")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    WARNING_FIELD_NUMBER: _ClassVar[int]
    TASK_FIELD_NUMBER: _ClassVar[int]
    success: bool
    warning: _common_pb2.Warning
    task: _common_pb2.Task
    def __init__(self, success: bool = ..., warning: _Optional[_Union[_common_pb2.Warning, _Mapping]] = ..., task: _Optional[_Union[_common_pb2.Task, _Mapping]] = ...) -> None: ...

class AlterTableRequest(_message.Message):
    __slots__ = ("configuration", "schema_name", "table", "drop_columns")
    class ConfigurationEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    DROP_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    configuration: _containers.ScalarMap[str, str]
    schema_name: str
    table: _common_pb2.Table
    drop_columns: bool
    def __init__(self, configuration: _Optional[_Mapping[str, str]] = ..., schema_name: _Optional[str] = ..., table: _Optional[_Union[_common_pb2.Table, _Mapping]] = ..., drop_columns: bool = ...) -> None: ...

class AlterTableResponse(_message.Message):
    __slots__ = ("success", "warning", "task")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    WARNING_FIELD_NUMBER: _ClassVar[int]
    TASK_FIELD_NUMBER: _ClassVar[int]
    success: bool
    warning: _common_pb2.Warning
    task: _common_pb2.Task
    def __init__(self, success: bool = ..., warning: _Optional[_Union[_common_pb2.Warning, _Mapping]] = ..., task: _Optional[_Union[_common_pb2.Task, _Mapping]] = ...) -> None: ...

class TruncateRequest(_message.Message):
    __slots__ = ("configuration", "schema_name", "table_name", "synced_column", "utc_delete_before", "soft")
    class ConfigurationEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    SYNCED_COLUMN_FIELD_NUMBER: _ClassVar[int]
    UTC_DELETE_BEFORE_FIELD_NUMBER: _ClassVar[int]
    SOFT_FIELD_NUMBER: _ClassVar[int]
    configuration: _containers.ScalarMap[str, str]
    schema_name: str
    table_name: str
    synced_column: str
    utc_delete_before: _timestamp_pb2.Timestamp
    soft: SoftTruncate
    def __init__(self, configuration: _Optional[_Mapping[str, str]] = ..., schema_name: _Optional[str] = ..., table_name: _Optional[str] = ..., synced_column: _Optional[str] = ..., utc_delete_before: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., soft: _Optional[_Union[SoftTruncate, _Mapping]] = ...) -> None: ...

class SoftTruncate(_message.Message):
    __slots__ = ("deleted_column",)
    DELETED_COLUMN_FIELD_NUMBER: _ClassVar[int]
    deleted_column: str
    def __init__(self, deleted_column: _Optional[str] = ...) -> None: ...

class TruncateResponse(_message.Message):
    __slots__ = ("success", "warning", "task")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    WARNING_FIELD_NUMBER: _ClassVar[int]
    TASK_FIELD_NUMBER: _ClassVar[int]
    success: bool
    warning: _common_pb2.Warning
    task: _common_pb2.Task
    def __init__(self, success: bool = ..., warning: _Optional[_Union[_common_pb2.Warning, _Mapping]] = ..., task: _Optional[_Union[_common_pb2.Task, _Mapping]] = ...) -> None: ...

class WriteBatchRequest(_message.Message):
    __slots__ = ("configuration", "schema_name", "table", "keys", "replace_files", "update_files", "delete_files", "file_params")
    class ConfigurationEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class KeysEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bytes
        def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    REPLACE_FILES_FIELD_NUMBER: _ClassVar[int]
    UPDATE_FILES_FIELD_NUMBER: _ClassVar[int]
    DELETE_FILES_FIELD_NUMBER: _ClassVar[int]
    FILE_PARAMS_FIELD_NUMBER: _ClassVar[int]
    configuration: _containers.ScalarMap[str, str]
    schema_name: str
    table: _common_pb2.Table
    keys: _containers.ScalarMap[str, bytes]
    replace_files: _containers.RepeatedScalarFieldContainer[str]
    update_files: _containers.RepeatedScalarFieldContainer[str]
    delete_files: _containers.RepeatedScalarFieldContainer[str]
    file_params: FileParams
    def __init__(self, configuration: _Optional[_Mapping[str, str]] = ..., schema_name: _Optional[str] = ..., table: _Optional[_Union[_common_pb2.Table, _Mapping]] = ..., keys: _Optional[_Mapping[str, bytes]] = ..., replace_files: _Optional[_Iterable[str]] = ..., update_files: _Optional[_Iterable[str]] = ..., delete_files: _Optional[_Iterable[str]] = ..., file_params: _Optional[_Union[FileParams, _Mapping]] = ...) -> None: ...

class WriteHistoryBatchRequest(_message.Message):
    __slots__ = ("configuration", "schema_name", "table", "keys", "earliest_start_files", "replace_files", "update_files", "delete_files", "file_params")
    class ConfigurationEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class KeysEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bytes
        def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    EARLIEST_START_FILES_FIELD_NUMBER: _ClassVar[int]
    REPLACE_FILES_FIELD_NUMBER: _ClassVar[int]
    UPDATE_FILES_FIELD_NUMBER: _ClassVar[int]
    DELETE_FILES_FIELD_NUMBER: _ClassVar[int]
    FILE_PARAMS_FIELD_NUMBER: _ClassVar[int]
    configuration: _containers.ScalarMap[str, str]
    schema_name: str
    table: _common_pb2.Table
    keys: _containers.ScalarMap[str, bytes]
    earliest_start_files: _containers.RepeatedScalarFieldContainer[str]
    replace_files: _containers.RepeatedScalarFieldContainer[str]
    update_files: _containers.RepeatedScalarFieldContainer[str]
    delete_files: _containers.RepeatedScalarFieldContainer[str]
    file_params: FileParams
    def __init__(self, configuration: _Optional[_Mapping[str, str]] = ..., schema_name: _Optional[str] = ..., table: _Optional[_Union[_common_pb2.Table, _Mapping]] = ..., keys: _Optional[_Mapping[str, bytes]] = ..., earliest_start_files: _Optional[_Iterable[str]] = ..., replace_files: _Optional[_Iterable[str]] = ..., update_files: _Optional[_Iterable[str]] = ..., delete_files: _Optional[_Iterable[str]] = ..., file_params: _Optional[_Union[FileParams, _Mapping]] = ...) -> None: ...

class FileParams(_message.Message):
    __slots__ = ("compression", "encryption", "null_string", "unmodified_string")
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_FIELD_NUMBER: _ClassVar[int]
    NULL_STRING_FIELD_NUMBER: _ClassVar[int]
    UNMODIFIED_STRING_FIELD_NUMBER: _ClassVar[int]
    compression: Compression
    encryption: Encryption
    null_string: str
    unmodified_string: str
    def __init__(self, compression: _Optional[_Union[Compression, str]] = ..., encryption: _Optional[_Union[Encryption, str]] = ..., null_string: _Optional[str] = ..., unmodified_string: _Optional[str] = ...) -> None: ...

class WriteBatchResponse(_message.Message):
    __slots__ = ("success", "warning", "task")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    WARNING_FIELD_NUMBER: _ClassVar[int]
    TASK_FIELD_NUMBER: _ClassVar[int]
    success: bool
    warning: _common_pb2.Warning
    task: _common_pb2.Task
    def __init__(self, success: bool = ..., warning: _Optional[_Union[_common_pb2.Warning, _Mapping]] = ..., task: _Optional[_Union[_common_pb2.Task, _Mapping]] = ...) -> None: ...

class MigrateRequest(_message.Message):
    __slots__ = ("configuration", "details")
    class ConfigurationEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    configuration: _containers.ScalarMap[str, str]
    details: MigrationDetails
    def __init__(self, configuration: _Optional[_Mapping[str, str]] = ..., details: _Optional[_Union[MigrationDetails, _Mapping]] = ...) -> None: ...

class MigrateResponse(_message.Message):
    __slots__ = ("success", "unsupported", "warning", "task")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_FIELD_NUMBER: _ClassVar[int]
    WARNING_FIELD_NUMBER: _ClassVar[int]
    TASK_FIELD_NUMBER: _ClassVar[int]
    success: bool
    unsupported: bool
    warning: _common_pb2.Warning
    task: _common_pb2.Task
    def __init__(self, success: bool = ..., unsupported: bool = ..., warning: _Optional[_Union[_common_pb2.Warning, _Mapping]] = ..., task: _Optional[_Union[_common_pb2.Task, _Mapping]] = ...) -> None: ...

class MigrationDetails(_message.Message):
    __slots__ = ("schema", "table", "drop", "copy", "rename", "add", "update_column_value", "table_sync_mode_migration")
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    DROP_FIELD_NUMBER: _ClassVar[int]
    COPY_FIELD_NUMBER: _ClassVar[int]
    RENAME_FIELD_NUMBER: _ClassVar[int]
    ADD_FIELD_NUMBER: _ClassVar[int]
    UPDATE_COLUMN_VALUE_FIELD_NUMBER: _ClassVar[int]
    TABLE_SYNC_MODE_MIGRATION_FIELD_NUMBER: _ClassVar[int]
    schema: str
    table: str
    drop: DropOperation
    copy: CopyOperation
    rename: RenameOperation
    add: AddOperation
    update_column_value: UpdateColumnValueOperation
    table_sync_mode_migration: TableSyncModeMigrationOperation
    def __init__(self, schema: _Optional[str] = ..., table: _Optional[str] = ..., drop: _Optional[_Union[DropOperation, _Mapping]] = ..., copy: _Optional[_Union[CopyOperation, _Mapping]] = ..., rename: _Optional[_Union[RenameOperation, _Mapping]] = ..., add: _Optional[_Union[AddOperation, _Mapping]] = ..., update_column_value: _Optional[_Union[UpdateColumnValueOperation, _Mapping]] = ..., table_sync_mode_migration: _Optional[_Union[TableSyncModeMigrationOperation, _Mapping]] = ...) -> None: ...

class DropOperation(_message.Message):
    __slots__ = ("drop_table", "drop_column_in_history_mode")
    DROP_TABLE_FIELD_NUMBER: _ClassVar[int]
    DROP_COLUMN_IN_HISTORY_MODE_FIELD_NUMBER: _ClassVar[int]
    drop_table: bool
    drop_column_in_history_mode: DropColumnInHistoryMode
    def __init__(self, drop_table: bool = ..., drop_column_in_history_mode: _Optional[_Union[DropColumnInHistoryMode, _Mapping]] = ...) -> None: ...

class DropColumnInHistoryMode(_message.Message):
    __slots__ = ("column", "operation_timestamp")
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    OPERATION_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    column: str
    operation_timestamp: str
    def __init__(self, column: _Optional[str] = ..., operation_timestamp: _Optional[str] = ...) -> None: ...

class CopyOperation(_message.Message):
    __slots__ = ("copy_table", "copy_column", "copy_table_to_history_mode")
    COPY_TABLE_FIELD_NUMBER: _ClassVar[int]
    COPY_COLUMN_FIELD_NUMBER: _ClassVar[int]
    COPY_TABLE_TO_HISTORY_MODE_FIELD_NUMBER: _ClassVar[int]
    copy_table: CopyTable
    copy_column: CopyColumn
    copy_table_to_history_mode: CopyTableToHistoryMode
    def __init__(self, copy_table: _Optional[_Union[CopyTable, _Mapping]] = ..., copy_column: _Optional[_Union[CopyColumn, _Mapping]] = ..., copy_table_to_history_mode: _Optional[_Union[CopyTableToHistoryMode, _Mapping]] = ...) -> None: ...

class CopyTable(_message.Message):
    __slots__ = ("from_table", "to_table")
    FROM_TABLE_FIELD_NUMBER: _ClassVar[int]
    TO_TABLE_FIELD_NUMBER: _ClassVar[int]
    from_table: str
    to_table: str
    def __init__(self, from_table: _Optional[str] = ..., to_table: _Optional[str] = ...) -> None: ...

class CopyColumn(_message.Message):
    __slots__ = ("from_column", "to_column")
    FROM_COLUMN_FIELD_NUMBER: _ClassVar[int]
    TO_COLUMN_FIELD_NUMBER: _ClassVar[int]
    from_column: str
    to_column: str
    def __init__(self, from_column: _Optional[str] = ..., to_column: _Optional[str] = ...) -> None: ...

class CopyTableToHistoryMode(_message.Message):
    __slots__ = ("from_table", "to_table", "soft_deleted_column")
    FROM_TABLE_FIELD_NUMBER: _ClassVar[int]
    TO_TABLE_FIELD_NUMBER: _ClassVar[int]
    SOFT_DELETED_COLUMN_FIELD_NUMBER: _ClassVar[int]
    from_table: str
    to_table: str
    soft_deleted_column: str
    def __init__(self, from_table: _Optional[str] = ..., to_table: _Optional[str] = ..., soft_deleted_column: _Optional[str] = ...) -> None: ...

class RenameOperation(_message.Message):
    __slots__ = ("rename_table", "rename_column")
    RENAME_TABLE_FIELD_NUMBER: _ClassVar[int]
    RENAME_COLUMN_FIELD_NUMBER: _ClassVar[int]
    rename_table: RenameTable
    rename_column: RenameColumn
    def __init__(self, rename_table: _Optional[_Union[RenameTable, _Mapping]] = ..., rename_column: _Optional[_Union[RenameColumn, _Mapping]] = ...) -> None: ...

class RenameTable(_message.Message):
    __slots__ = ("from_table", "to_table")
    FROM_TABLE_FIELD_NUMBER: _ClassVar[int]
    TO_TABLE_FIELD_NUMBER: _ClassVar[int]
    from_table: str
    to_table: str
    def __init__(self, from_table: _Optional[str] = ..., to_table: _Optional[str] = ...) -> None: ...

class RenameColumn(_message.Message):
    __slots__ = ("from_column", "to_column")
    FROM_COLUMN_FIELD_NUMBER: _ClassVar[int]
    TO_COLUMN_FIELD_NUMBER: _ClassVar[int]
    from_column: str
    to_column: str
    def __init__(self, from_column: _Optional[str] = ..., to_column: _Optional[str] = ...) -> None: ...

class AddOperation(_message.Message):
    __slots__ = ("add_column_in_history_mode", "add_column_with_default_value")
    ADD_COLUMN_IN_HISTORY_MODE_FIELD_NUMBER: _ClassVar[int]
    ADD_COLUMN_WITH_DEFAULT_VALUE_FIELD_NUMBER: _ClassVar[int]
    add_column_in_history_mode: AddColumnInHistoryMode
    add_column_with_default_value: AddColumnWithDefaultValue
    def __init__(self, add_column_in_history_mode: _Optional[_Union[AddColumnInHistoryMode, _Mapping]] = ..., add_column_with_default_value: _Optional[_Union[AddColumnWithDefaultValue, _Mapping]] = ...) -> None: ...

class AddColumnWithDefaultValue(_message.Message):
    __slots__ = ("column", "column_type", "default_value")
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    COLUMN_TYPE_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_VALUE_FIELD_NUMBER: _ClassVar[int]
    column: str
    column_type: _common_pb2.DataType
    default_value: str
    def __init__(self, column: _Optional[str] = ..., column_type: _Optional[_Union[_common_pb2.DataType, str]] = ..., default_value: _Optional[str] = ...) -> None: ...

class AddColumnInHistoryMode(_message.Message):
    __slots__ = ("column", "column_type", "default_value", "operation_timestamp")
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    COLUMN_TYPE_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_VALUE_FIELD_NUMBER: _ClassVar[int]
    OPERATION_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    column: str
    column_type: _common_pb2.DataType
    default_value: str
    operation_timestamp: str
    def __init__(self, column: _Optional[str] = ..., column_type: _Optional[_Union[_common_pb2.DataType, str]] = ..., default_value: _Optional[str] = ..., operation_timestamp: _Optional[str] = ...) -> None: ...

class UpdateColumnValueOperation(_message.Message):
    __slots__ = ("column", "value")
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    column: str
    value: str
    def __init__(self, column: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class TableSyncModeMigrationOperation(_message.Message):
    __slots__ = ("type", "soft_deleted_column", "keep_deleted_rows")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SOFT_DELETED_COLUMN_FIELD_NUMBER: _ClassVar[int]
    KEEP_DELETED_ROWS_FIELD_NUMBER: _ClassVar[int]
    type: TableSyncModeMigrationType
    soft_deleted_column: str
    keep_deleted_rows: bool
    def __init__(self, type: _Optional[_Union[TableSyncModeMigrationType, str]] = ..., soft_deleted_column: _Optional[str] = ..., keep_deleted_rows: bool = ...) -> None: ...
