import logging
import typing as t

import sqlalchemy as sa
from attr import Factory
from attrs import define
from toolz import dissoc

from cratedb_fivetran_destination.model import (
    FieldMap,
    SqlBag,
    SqlStatement,
    TableAddress,
    TableInfo,
    TypeMap,
)
from cratedb_fivetran_destination.schema_migration_helper import (
    FIVETRAN_ACTIVE,
    FIVETRAN_END,
    FIVETRAN_START,
)
from fivetran_sdk import common_pb2

logger = logging.getLogger()


@define
class UpsertStatement:
    """
    Manage and render an SQL upsert statement suitable for CrateDB.

    INSERT INTO ... ON CONFLICT ... DO UPDATE SET ...
    """

    table: TableInfo
    record: t.Dict[str, t.Any] = Factory(dict)

    @property
    def data(self):
        """
        The full record without primary key data.
        """
        return dissoc(self.record, *self.table.primary_keys)

    def to_sql(self) -> SqlBag:
        """
        Render statement to SQL.
        """
        return SqlBag().add(f"""
        INSERT INTO {self.table.fullname}
        ({", ".join([f'"{key}"' for key in self.record.keys()])})
        VALUES ({", ".join([f":{key}" for key in self.record.keys()])})
        ON CONFLICT ({", ".join(self.table.primary_keys)}) DO UPDATE
        SET {", ".join([f'"{key}"="excluded"."{key}"' for key in self.data.keys()])}
        """)  # noqa: S608


@define
class UpdateStatement:
    """
    Manage and render an SQL update statement.

    UPDATE ... SET ... WHERE ...
    """

    table: TableInfo
    record: t.Dict[str, t.Any] = Factory(dict)

    @property
    def data(self):
        """
        The full record without primary key data.
        """
        return dissoc(self.record, *self.table.primary_keys)

    def to_sql(self) -> SqlBag:
        """
        Render statement to SQL.
        """
        return SqlBag().add(f"""
        UPDATE {self.table.fullname}
        SET {", ".join([f'"{key}" = :{key}' for key in self.data.keys()])}
        WHERE {" AND ".join([f'"{key}" = :{key}' for key in self.table.primary_keys])}
        """)  # noqa: S608


@define
class DeleteStatement:
    """
    Manage and render an SQL delete statement.

    DELETE FROM ... WHERE ...
    """

    table: TableInfo
    record: t.Dict[str, t.Any] = Factory(dict)

    def to_sql(self) -> SqlBag:
        """
        Render statement to SQL.
        """
        return SqlBag().add(f"""
        DELETE FROM {self.table.fullname}
        WHERE {" AND ".join([f'"{key}" = :{key}' for key in self.table.primary_keys])}
        """)  # noqa: S608


@define
class AlterTableInplaceStatements:
    """
    Manage and render a procedure of SQL statements for altering/migrating a table schema.
    """

    table: TableInfo
    columns_new: t.List[common_pb2.Column] = Factory(list)
    columns_changed: t.List[common_pb2.Column] = Factory(list)

    def to_sql(self) -> SqlBag:
        sqlbag = SqlBag()

        if not self.columns_new and not self.columns_changed:
            return sqlbag

        # Translate "columns changed" instructions into migration operation
        # based on altering and copying using `UPDATE ... SET ...`.
        for column in self.columns_changed:
            column_name = FieldMap.to_cratedb(column.name)
            column_name_temporary = column_name + "_alter_tmp"
            type_ = TypeMap.to_cratedb(column.type, column.params)
            sqlbag.add(
                f'ALTER TABLE {self.table.fullname} ADD COLUMN "{column_name_temporary}" {type_};'
            )
            sqlbag.add(
                f'UPDATE {self.table.fullname} SET "{column_name_temporary}" = "{column_name}"::{type_};'  # noqa: S608, E501
            )
            sqlbag.add(f'ALTER TABLE {self.table.fullname} DROP "{column_name}";')
            sqlbag.add(
                f'ALTER TABLE {self.table.fullname} RENAME COLUMN "{column_name_temporary}" TO "{column_name}";'  # noqa: E501
            )

        # Translate "new column" instructions into `ALTER TABLE ... ADD ...` clauses.
        if self.columns_new:
            alter_add_ops: t.List[str] = []
            for column in self.columns_new:
                alter_add_ops.append(f"ADD {self.column_definition(column)}")
            sqlbag.add(f"ALTER TABLE {self.table.fullname} {', '.join(alter_add_ops)};")

        return sqlbag

    @staticmethod
    def column_definition(column):
        field = FieldMap.to_cratedb(column.name)
        type_ = TypeMap.to_cratedb(column.type, column.params)
        return f"{field} {type_}"


@define
class AlterTableRecreateStatements:
    """
    Manage and render a procedure of SQL statements for recreating a table with a new schema.

    The procedure will create a new table, transfer data, and swap tables.
    It is needed for propagating primary key column changes.
    """

    address_effective: TableAddress
    address_temporary: TableAddress
    columns_old: t.List[common_pb2.Column] = Factory(list)
    columns_new: t.List[common_pb2.Column] = Factory(list)

    def to_sql(self) -> SqlBag:
        # Validate positional mapping assumption
        if len(self.columns_old) != len(self.columns_new):
            raise ValueError(
                f"Column count mismatch: old table has {len(self.columns_old)} columns, "
                f"new table has {len(self.columns_new)} columns. "
                f"Recreate operation requires matching column counts."
            )

        sqlbag = SqlBag()

        table_real = self.address_effective.fullname
        table_temp = self.address_temporary.fullname

        # Put the source table into read-only mode at the beginning of the following operations.
        sqlbag.add(f'ALTER TABLE {table_real} SET ("blocks.write"=true);')

        # Define transform operation involving a temporary table copy and swap.
        sqlbag.add(
            f"""
        INSERT INTO
            {table_temp}
            ({", ".join([f'"{FieldMap.to_cratedb(col.name)}"' for col in self.columns_new])})
            (SELECT {", ".join([f'"{FieldMap.to_cratedb(col.name)}"' for col in self.columns_old])} FROM {table_real})
        """  # noqa: S608, E501
        )

        # Put the source table into read+write mode again,
        # and replace it with the new newly populated temporary table.
        sqlbag.add(f'ALTER TABLE {table_real} RESET ("blocks.write");')
        sqlbag.add(f"ALTER CLUSTER SWAP TABLE {table_temp} TO {table_real} WITH (drop_source=true)")

        return sqlbag


@define
class EarliestStartHistoryStatements:
    """
    Manage and render SQL statements suitable for processing `earliest_start_files`.

    DELETE FROM ...
        WHERE pk1 = <val> {AND  pk2 = <val>...} AND _fivetran_start >= timestamp_value

    UPDATE ... SET _fivetran_active = FALSE, _fivetran_end = _fivetran_start - 1 msec
        WHERE _fivetran_active = TRUE AND pk1 = <val> {AND  pk2 = <val>...}

    https://github.com/fivetran/fivetran_partner_sdk/blob/main/how-to-handle-history-mode-batch-files.md#earliest_start_files
    """

    table: TableInfo
    records: t.Iterable[t.Dict[str, t.Any]]
    records_list: t.List[t.Dict[str, t.Any]] = Factory(list)

    def __attrs_post_init__(self):
        self.records_list = list(self.records)

    def to_sql(self) -> SqlBag:
        """
        Render statement to SQL.
        """
        sql = SqlBag()
        sql.add(self.hard_delete_with_timestamp())
        sql.add(self.update_history_active())
        return sql

    def hard_delete_with_timestamp(self) -> t.Optional[SqlStatement]:
        """
        Generate DELETE statements such as:

        DELETE FROM "foo"."bar" WHERE
            ("id" = 1 AND "_fivetran_start" >= '1646455512123456789')
         OR ("id" = 2 AND "_fivetran_start" >= '1680784200234567890')
         OR ("id" = 3 AND "_fivetran_start" >= '1680784300234567890')

        This procedure combines primary key equality checks with a timestamp comparison
        for each row, matching the behaviour of the Java `writeDelete` method which uses
        AND conditions between primary keys and the timestamp filter.
        """
        # Build primary key equality conditions and timestamp condition (AND).
        conditions = []
        params = {}
        for index, record in enumerate(self.records_list):
            condition = []
            for pk_index, pk in enumerate(self.table.primary_keys):
                if pk == FIVETRAN_START:
                    continue
                param_name = f"pk{index}{pk_index}"
                condition.append(f'"{pk}" = :{param_name}')
                params[param_name] = record[pk]

            param_name = f"ts{index}"
            condition.append(f'"{FIVETRAN_START}" >= CAST(:{param_name} AS TIMESTAMP)')
            params[param_name] = record[FIVETRAN_START]

            conditions.append(" AND ".join(condition))

        if not conditions:
            return None

        # Build row conditions (OR).
        conditions = [f"({condition})" for condition in conditions]
        sql = f"DELETE FROM {self.table.fullname} WHERE {' OR '.join(conditions)}"  # noqa: S608
        return SqlStatement(sql, parameters=params)

    def update_history_active(self) -> SqlBag:
        """
        Generate UPDATE statements such as:

            ALTER TABLE "foo"."bar"
            UPDATE
                "_fivetran_active" = FALSE,
                "_fivetran_end" = CASE
                    WHEN "id" = 1 THEN '1646455512123456788'
                    WHEN "id" = 2 THEN '1680784200234567889'
                    WHEN "id" = 3 THEN '1680786000345678900'
                END
            WHERE "id" IN (1, 2, 3)
                AND "_fivetran_active" = TRUE

        This procedure updates history records by setting `_fivetran_active` to `FALSE`
        and `_fivetran_end` to the timestamp value from the data source,
        typically `_fivetran_start - 1`.

        TODO: Review: The code below generates individual UPDATE statements per record instead of
              the single SQL statement outlined above. This is more straight-forward, but might
              be less efficient.
        """
        sql_bag = SqlBag()
        for index, record in enumerate(self.records_list):
            condition = []
            params = {}
            for pk_index, pk in enumerate(self.table.primary_keys):
                if pk == FIVETRAN_START:
                    continue
                param_name = f"pk{index}{pk_index}"
                condition.append(f'"{pk}" = :{param_name}')
                params[param_name] = record[pk]

            ts_param_name = f"ts{index}"
            params[ts_param_name] = record[FIVETRAN_START]

            sql_bag.add(
                SqlStatement(
                    f"""
            UPDATE {self.table.fullname}
            SET
                {FIVETRAN_ACTIVE} = FALSE,
                {FIVETRAN_END} = CAST(:{ts_param_name} AS TIMESTAMP) - INTERVAL '1 millisecond'
            WHERE
                {FIVETRAN_ACTIVE} = TRUE
            AND {" AND ".join(condition)}
            """,  # noqa: S608
                    params,
                )
            )
        return sql_bag


@define
class WriteBatchProcessor:
    engine: sa.Engine

    def process(
        self,
        table_info: TableInfo,
        upsert_records: t.Iterable[t.Dict[str, t.Any]],
        update_records: t.Iterable[t.Dict[str, t.Any]],
        delete_records: t.Iterable[t.Dict[str, t.Any]],
    ):
        with self.engine.connect() as connection:
            # Apply upsert SQL statements.
            # `INSERT INTO ... ON CONFLICT ... DO UPDATE SET ...`.
            process_records(
                connection,
                upsert_records,
                lambda record: UpsertStatement(table=table_info, record=record).to_sql(),
            )

            process_records(
                connection,
                update_records,
                lambda record: UpdateStatement(table=table_info, record=record).to_sql(),
            )

            process_records(
                connection,
                delete_records,
                lambda record: DeleteStatement(table=table_info, record=record).to_sql(),
            )


@define
class WriteHistoryBatchProcessor:
    """
    History mode allows to capture every available version of each record.

    The following types of files are a part of the WriteHistoryBatchRequest gRPC call.
    These files must be processed in the exact order as described in the following subsections.

    earliest_start_files, update_files, replace_files, delete_files

    - https://github.com/fivetran/fivetran_partner_sdk/blob/main/how-to-handle-history-mode-batch-files.md
    - https://fivetran.com/docs/using-fivetran/features#historymode
    """

    engine: sa.Engine

    def process(
        self,
        table_info: TableInfo,
        earliest_start_records: t.Iterable[t.Dict[str, t.Any]],
        update_records: t.Iterable[t.Dict[str, t.Any]],
        replace_records: t.Iterable[t.Dict[str, t.Any]],
        delete_records: t.Iterable[t.Dict[str, t.Any]],
    ):
        with self.engine.connect() as connection:
            EarliestStartHistoryStatements(
                table=table_info, records=earliest_start_records
            ).to_sql().execute(connection)

            process_records(
                connection,
                update_records,
                lambda record: UpdateStatement(table=table_info, record=record).to_sql(),
            )

            process_records(
                connection,
                replace_records,
                lambda record: UpsertStatement(table=table_info, record=record).to_sql(),
            )

            process_records(
                connection,
                delete_records,
                lambda record: DeleteStatement(table=table_info, record=record).to_sql(),
            )


def process_records(connection, records, converter):
    for record in records:
        # DML statements are always singular, because they are accompanied with a `record`.
        sql = str(converter(record).statements[0])
        try:
            connection.execute(sa.text(sql), record)
        except sa.exc.ProgrammingError as ex:
            logger.error(f"Processing database operation failed: {ex}")
            raise
