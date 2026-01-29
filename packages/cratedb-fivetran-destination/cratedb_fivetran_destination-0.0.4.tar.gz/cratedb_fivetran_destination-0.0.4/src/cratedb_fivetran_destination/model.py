import typing as t
from textwrap import dedent

import dateutil
import sqlalchemy as sa
from attr import Factory
from attrs import define
from sqlalchemy_cratedb import ObjectType
from sqlalchemy_cratedb.type.object import ObjectTypeImpl

from cratedb_fivetran_destination.dictx import OrderedDictX
from fivetran_sdk import common_pb2
from fivetran_sdk.common_pb2 import DataType


class FieldMap:
    """
    Manage special knowledge about CrateDB field names.
    """

    # Map special column names, because CrateDB does not allow `_` prefixes.
    field_map = {
        "_fivetran_id": "__fivetran_id",
        "_fivetran_synced": "__fivetran_synced",
        "_fivetran_start": "__fivetran_start",
        "_fivetran_end": "__fivetran_end",
        "_fivetran_active": "__fivetran_active",
        "_fivetran_deleted": "__fivetran_deleted",
    }

    @classmethod
    def rename_keys(cls, record):
        """
        Rename keys according to the field map.
        """
        record = OrderedDictX(record)
        for key, value in cls.field_map.items():
            if key in record:
                record.rename_key(key, value)
        return record

    @classmethod
    def to_cratedb(cls, fivetran_field):
        """
        Convert a Fivetran field name into a CrateDB field name.
        """
        return cls.field_map.get(fivetran_field, fivetran_field)

    @classmethod
    def to_fivetran(cls, cratedb_field):
        """
        Convert a CrateDB field name into a Fivetran field name.
        """
        # TODO: Compute reverse map only once.
        reverse_map = dict(zip(cls.field_map.values(), cls.field_map.keys()))
        return reverse_map.get(cratedb_field, cratedb_field)


class TypeMap:
    """
    Map Fivetran types to CrateDB types and back.
    """

    cratedb_default = sa.Text()
    fivetran_default = DataType.UNSPECIFIED

    fivetran_map = {
        DataType.UNSPECIFIED: sa.Text(),
        DataType.BOOLEAN: sa.Boolean(),
        DataType.SHORT: sa.SmallInteger(),
        DataType.INT: sa.Integer(),
        DataType.LONG: sa.BigInteger(),
        DataType.FLOAT: sa.Float(),
        DataType.DOUBLE: sa.Double(),
        # CrateDB can not store `DATE` types, so converge to `TIMESTAMP`.
        DataType.NAIVE_DATE: sa.TIMESTAMP(),
        DataType.NAIVE_DATETIME: sa.TIMESTAMP(),
        DataType.NAIVE_TIME: sa.TIMESTAMP(),
        DataType.UTC_DATETIME: sa.TIMESTAMP(),
        # TODO: The parameters are coming from the API, here `input_fivetran.json`.
        #       How to loop them into this type resolution machinery?
        DataType.DECIMAL: sa.DECIMAL(6, 3),
        DataType.BINARY: sa.Text(),
        DataType.STRING: sa.String(),
        DataType.JSON: ObjectTypeImpl(),
        DataType.XML: sa.String(),
    }

    cratedb_map = {
        sa.Text: DataType.STRING,
        sa.TEXT: DataType.STRING,
        sa.VARCHAR: DataType.STRING,
        sa.Boolean: DataType.BOOLEAN,
        sa.BOOLEAN: DataType.BOOLEAN,
        sa.SmallInteger: DataType.SHORT,
        sa.Integer: DataType.INT,
        sa.BigInteger: DataType.LONG,
        sa.SMALLINT: DataType.SHORT,
        sa.INTEGER: DataType.INT,
        sa.BIGINT: DataType.LONG,
        sa.Float: DataType.FLOAT,
        sa.FLOAT: DataType.FLOAT,
        sa.Double: DataType.DOUBLE,
        sa.DOUBLE: DataType.DOUBLE,
        sa.DOUBLE_PRECISION: DataType.DOUBLE,
        sa.Date: DataType.NAIVE_DATE,
        sa.DATE: DataType.NAIVE_DATE,
        # FIXME: Which one to choose?
        #        Need better inspection about aware/unaware datetime objects?
        # sa.DateTime: DataType.NAIVE_DATETIME,
        sa.DateTime: DataType.UTC_DATETIME,
        sa.DATETIME: DataType.UTC_DATETIME,
        sa.Time: DataType.NAIVE_TIME,
        sa.TIME: DataType.NAIVE_TIME,
        sa.Numeric: DataType.DECIMAL,
        sa.DECIMAL: DataType.DECIMAL,
        sa.LargeBinary: DataType.BINARY,
        sa.BINARY: DataType.BINARY,
        ObjectType: DataType.JSON,
        ObjectTypeImpl: DataType.JSON,
        # FIXME: What about Arrays?
    }

    @classmethod
    def to_cratedb(cls, fivetran_type, fivetran_params=None):
        """
        Convert a Fivetran type into a CrateDB type.
        """
        # TODO: Introduce parameter handling to type mappers.
        return cls.fivetran_map.get(fivetran_type, cls.cratedb_default)

    @classmethod
    def to_fivetran(cls, cratedb_type):
        """
        Convert a CrateDB type into a Fivetran type.
        """
        return cls.cratedb_map.get(type(cratedb_type), cls.fivetran_default)


class FivetranKnowledge:
    """
    Manage special knowledge about Fivetran.

    Fivetran uses special values for designating NULL and CDC-unmodified values.
    """

    NULL_STRING = "null-m8yilkvPsNulehxl2G6pmSQ3G3WWdLP"
    UNMODIFIED_STRING = "unmod-NcK9NIjPUutCsz4mjOQQztbnwnE1sY3"

    @classmethod
    def replace_values(cls, record):
        rm_list = []
        for key, value in record.items():
            if value == cls.NULL_STRING:
                record[key] = None
            elif value == cls.UNMODIFIED_STRING:
                rm_list.append(key)
        for rm in rm_list:
            record.pop(rm)


class CrateDBKnowledge:
    """
    Manage special knowledge about CrateDB.

    CrateDB can't store values of the `TIME` type, so we selected to store it as `DATETIME`
    This routine converges the value.
    """

    @classmethod
    def replace_values(cls, request, record):
        for column in request.table.columns:
            if column.type == common_pb2.DataType.NAIVE_TIME and column.name in record:
                value = record[column.name]
                if value is None:
                    continue
                try:
                    obj = dateutil.parser.parse(value)
                except (TypeError, ValueError, dateutil.parser.ParserError) as e:
                    raise ValueError(
                        f"Invalid NAIVE_TIME value '{value}' for column '{column.name}': {e}"
                    ) from e
                obj = obj.replace(year=1970, month=1, day=1)
                # Calculate milliseconds since midnight (timezone-independent).
                ms = (
                    obj.hour * 3600 + obj.minute * 60 + obj.second
                ) * 1000 + obj.microsecond // 1000
                record[column.name] = str(ms)


@define
class TableInfo:
    """
    Manage information about a database table.
    """

    fullname: str
    primary_keys: t.List[str] = Factory(list)


@define
class TableAddress:
    """
    Manage the location of a database table.
    """

    schema_name: str
    table_name: str

    @property
    def fullname(self) -> str:
        return f'''"{self.schema_name}"."{self.table_name}"'''


@define
class SqlStatement:
    expression: str
    parameters: t.Dict[str, t.Any] = Factory(dict)

    def __str__(self) -> str:
        return self.expression


@define
class SqlBag:
    """
    A little bag of multiple SQL statements.
    """

    statements: t.List[SqlStatement] = Factory(list)

    def __bool__(self):
        return bool(self.statements)

    def add(self, sql: t.Union[str, "SqlBag", SqlStatement, None]):
        if sql is None:
            return self
        if isinstance(sql, str):
            self.statements.append(SqlStatement(dedent(sql).strip()))
        elif isinstance(sql, SqlStatement):
            self.statements.append(sql)
        elif isinstance(sql, SqlBag):
            self.statements += sql.statements
        else:
            raise TypeError(
                f'Input SQL must be str, SqlBag, or SqlStatement, not "{type(sql).__name__}"'
            )
        return self

    def execute(self, connection: sa.Connection):
        for stmt in self.statements:
            connection.execute(sa.text(stmt.expression), parameters=stmt.parameters)


class FivetranTable:
    """Provide helper methods for Fivetran tables."""

    @classmethod
    def pk_column_names(cls, table: common_pb2.Table) -> t.List[str]:
        """Return list of primary keys column names."""
        return [column.name for column in table.columns if column.primary_key]

    @classmethod
    def pk_equals(cls, t1: common_pb2.Table, t2: common_pb2.Table) -> bool:
        """Return whether two tables have the same primary keys."""
        return cls.pk_column_names(t1) == cls.pk_column_names(t2)
