# ruff: noqa: E501,S608
# https://github.com/fivetran/fivetran_partner_sdk/blob/main/examples/destination_connector/python/schema_migration_helper.py
import contextlib
import typing as t
from copy import deepcopy

import sqlalchemy as sa

from cratedb_fivetran_destination.model import FieldMap, SqlBag, SqlStatement, TypeMap
from cratedb_fivetran_destination.util import LOG_INFO, LOG_WARNING, log_message
from fivetran_sdk import common_pb2, destination_sdk_pb2

# Constants for system columns
FIVETRAN_START = "__fivetran_start"
FIVETRAN_END = "__fivetran_end"
FIVETRAN_ACTIVE = "__fivetran_active"
FIVETRAN_DELETED = "__fivetran_deleted"
FIVETRAN_SYNCED = "__fivetran_synced"

MIN_TIMESTAMP = "0000-01-01 00:00:00"
MAX_TIMESTAMP = "9999-12-31 23:59:59"


class SchemaMigrationHelper:
    """Helper class for handling migration operations"""

    def __init__(self, engine: sa.Engine):
        self.engine = engine
        self.schema_helper = TableSchemaHelper(engine=self.engine)

    def handle_drop(self, drop_op, schema, table, table_obj: common_pb2.Table):
        """
        Handles drop operations (drop table, drop column in history mode).
        """
        entity_case = drop_op.WhichOneof("entity")

        if entity_case == "drop_table":
            """
            This migration should drop the specified table.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#drop_table
            """
            sql = f'DROP TABLE "{schema}"."{table}"'
            with self.engine.connect() as conn:
                conn.execute(sa.text(sql))

            log_message(LOG_INFO, f"[Migrate:Drop] Dropping table {schema}.{table}")
            return destination_sdk_pb2.MigrateResponse(success=True)

        if entity_case == "drop_column_in_history_mode":
            """
            This migration records the history of a column drop operation in history mode.
            Rather than physically dropping the column, it maintains the column with NULL
            values for new records to preserve historical data.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#drop_column_in_history_mode
            """
            drop_column = drop_op.drop_column_in_history_mode

            column_name = drop_column.column
            operation_timestamp = drop_column.operation_timestamp

            # 0. Validate table is non-empty and `max(_fivetran_start) < operation_timestamp`.
            try:
                self._validate_history_table(schema, table, operation_timestamp)
            except ValueError as e:
                message = e.args[0]
                log_message(
                    LOG_WARNING,
                    f"[Migrate:DropColumnHistory] table={schema}.{table} column={column_name}: {message}",
                )
                return destination_sdk_pb2.MigrateResponse(
                    success=False,
                    warning=common_pb2.Warning(message=message),
                )

            # Compute lists of columns.
            all_columns, unchanged_columns = TableMetadataHelper.column_lists(
                table_obj, modulo_column_name=column_name
            )

            sql_bag = SqlBag()

            # 1. Insert new rows to record the history of the DDL operation.
            sql_bag.add(
                SqlStatement(
                    f"""
            INSERT INTO "{schema}"."{table}" ({", ".join(all_columns)})
            (
              SELECT
                {", ".join(unchanged_columns)},
                NULL AS "{column_name}",
                CAST(:operation_timestamp AS TIMESTAMP) AS {FIVETRAN_START}
              FROM "{schema}"."{table}"
              WHERE {FIVETRAN_ACTIVE} = TRUE
                AND "{column_name}" IS NOT NULL
                AND {FIVETRAN_START} < CAST(:operation_timestamp AS TIMESTAMP)
            );
            """,
                    {"operation_timestamp": operation_timestamp},
                )
            )

            # 2. Update the newly added row with the `operation_timestamp`.
            # This step is important in case of source connector sends multiple DROP_COLUMN_IN_HISTORY_MODE
            # operations with the same operation_timestamp. It will ensure, we only record history once
            # for that timestamp.
            sql_bag.add(
                SqlStatement(
                    f"""
            UPDATE "{schema}"."{table}"
            SET "{column_name}" = NULL
            WHERE {FIVETRAN_START} = CAST(:operation_timestamp AS TIMESTAMP);
            """,
                    {"operation_timestamp": operation_timestamp},
                )
            )

            # 3. Update the previous record's `_fivetran_end` to `(operation timestamp) - 1ms`
            # and set `_fivetran_active` to `FALSE`.
            sql_bag.add(
                SqlStatement(
                    f"""
            UPDATE "{schema}"."{table}"
               SET
                 {FIVETRAN_END} = CAST(:operation_timestamp AS TIMESTAMP) - INTERVAL '1 millisecond',
                 {FIVETRAN_ACTIVE} = FALSE
               WHERE {FIVETRAN_ACTIVE} = TRUE
                 AND "{column_name}" IS NOT NULL
                 AND {FIVETRAN_START} < CAST(:operation_timestamp AS TIMESTAMP);
            """,
                    {"operation_timestamp": operation_timestamp},
                )
            )
            with self.engine.connect() as conn:
                sql_bag.execute(conn)

            log_message(
                LOG_INFO,
                f"[Migrate:DropColumnHistory] table={schema}.{table} column={drop_column.column} op_ts={drop_column.operation_timestamp}",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        log_message(LOG_WARNING, "[Migrate:Drop] No drop entity specified")
        return destination_sdk_pb2.MigrateResponse(unsupported=True)

    def handle_copy(self, copy_op, schema, table, table_obj: common_pb2.Table):
        """Handles copy operations (copy table, copy column, copy table to history mode)."""
        entity_case = copy_op.WhichOneof("entity")

        if entity_case == "copy_table":
            """
            This migration should create a new table and copy the data from the source table to the destination table.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#copy_table
            """
            copy_table = copy_op.copy_table
            sql = (
                f'CREATE TABLE "{schema}"."{copy_table.to_table}" '
                f'AS SELECT * FROM "{schema}"."{copy_table.from_table}"'
            )
            with self.engine.connect() as conn:
                conn.execute(sa.text(sql))

            log_message(
                LOG_INFO,
                f"[Migrate:CopyTable] from={copy_table.from_table} to={copy_table.to_table} in schema={schema}",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        if entity_case == "copy_column":
            """
            This migration should add a new column and copy the data from the source column to the destination column.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#copy_column
            """
            sql_bag = SqlBag()
            copy_column = copy_op.copy_column
            for col in table_obj.columns:
                if col.name == copy_column.from_column:
                    new_col = type(col)()
                    new_col.CopyFrom(col)
                    new_col.name = copy_column.to_column
                    table_obj.columns.add().CopyFrom(new_col)
                    type_ = TypeMap.to_cratedb(new_col.type, new_col.params)
                    # 1. Add the new column with the same type as the old column.
                    sql_bag.add(
                        f'ALTER TABLE "{schema}"."{table}" ADD COLUMN "{new_col.name}" {type_};'
                    )
                    # 2. Update the new column with the values from the old column.
                    sql_bag.add(f'UPDATE "{schema}"."{table}" SET "{new_col.name}"="{col.name}";')
                    break

            if sql_bag:
                with self.engine.connect() as conn:
                    sql_bag.execute(conn)
                log_message(
                    LOG_INFO,
                    f"[Migrate:CopyColumn] table={schema}.{table} from_col={copy_column.from_column} to_col={copy_column.to_column}",
                )
                return destination_sdk_pb2.MigrateResponse(success=True)
            log_message(
                LOG_WARNING,
                f"[Migrate:CopyColumn] table={schema}.{table} from_col={copy_column.from_column} to_col={copy_column.to_column} Source column not found",
            )
            return destination_sdk_pb2.MigrateResponse(
                success=False, warning=common_pb2.Warning("Source column not found")
            )

        if entity_case == "copy_table_to_history_mode":
            """
            This migration should copy an existing table from a non-history mode to a new table in history mode.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#copy_table_to_history_mode
            """
            copy_table = copy_op.copy_table_to_history_mode
            soft_deleted_column = FieldMap.to_cratedb(copy_table.soft_deleted_column)

            with self.engine.connect() as conn:
                # 1. Create a new table with the new name and add the history mode columns.
                # 2. Copy the data from the old table to the new table.
                conn.execute(
                    sa.text(
                        f'CREATE TABLE "{schema}"."{copy_table.to_table}" '
                        f'AS SELECT * FROM "{schema}"."{copy_table.from_table}"'
                    )
                )

                # 3. Follow steps in the sync mode migration.
                # - SOFT_DELETE_TO_HISTORY if soft_deleted_column is not null, or
                # - LIVE_TO_HISTORY in order to migrate it to history mode.
                if copy_table.soft_deleted_column:
                    self._table_soft_delete_to_history(
                        schema, copy_table.to_table, soft_deleted_column
                    )
                else:
                    self._table_live_to_history(schema, copy_table.to_table)

            log_message(
                LOG_INFO,
                f"[Migrate:CopyTableToHistoryMode] from={copy_table.from_table} to={copy_table.to_table} soft_deleted_column={copy_table.soft_deleted_column}",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        log_message(LOG_WARNING, "[Migrate:Copy] No copy entity specified")
        return destination_sdk_pb2.MigrateResponse(unsupported=True)

    def handle_rename(self, rename_op, schema, table):
        """Handles rename operations (rename table, rename column)."""
        entity_case = rename_op.WhichOneof("entity")

        if entity_case == "rename_table":
            """
            This migration should rename the specified table in the schema.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#rename_table
            """
            rt = rename_op.rename_table
            sql = f'ALTER TABLE "{schema}"."{rt.from_table}" RENAME TO "{rt.to_table}";'
            with self.engine.connect() as conn:
                conn.execute(sa.text(sql))

            log_message(
                LOG_INFO,
                f"[Migrate:RenameTable] from={rt.from_table} to={rt.to_table} schema={schema}",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        if entity_case == "rename_column":
            """
            This migration should rename the specified column in the table.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#rename_column
            """
            rename_column = rename_op.rename_column
            sql = f'ALTER TABLE "{schema}"."{table}" RENAME COLUMN "{rename_column.from_column}" TO "{rename_column.to_column}";'
            with self.engine.connect() as conn:
                conn.execute(sa.text(sql))

            log_message(
                LOG_INFO,
                f"[Migrate:RenameColumn] table={schema}.{table} from_col={rename_column.from_column} to_col={rename_column.to_column}",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        log_message(LOG_WARNING, "[Migrate:Rename] No rename entity specified")
        return destination_sdk_pb2.MigrateResponse(unsupported=True)

    def handle_add(self, add_op, schema, table, table_obj: common_pb2.Table):
        """
        Handles add operations (add column in history mode, add column with default value).
        """
        entity_case = add_op.WhichOneof("entity")

        # Add a column to history-mode tables while preserving historical record integrity.
        if entity_case == "add_column_in_history_mode":
            """
            This migration should add a column to a table in history mode.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#add_column_in_history_mode
            """
            add_col_history_mode = add_op.add_column_in_history_mode

            column_name = add_col_history_mode.column
            column_type = TypeMap.to_cratedb(add_col_history_mode.column_type)
            default_value = add_col_history_mode.default_value
            operation_timestamp = add_col_history_mode.operation_timestamp

            sql_bag = SqlBag()

            # 0. Validate table is non-empty and `max(_fivetran_start) < operation_timestamp`.
            try:
                self._validate_history_table(schema, table, operation_timestamp)
            except ValueError as e:
                message = e.args[0]
                log_message(
                    LOG_WARNING,
                    f"[Migrate:AddColumnHistory] table={schema}.{table} column={column_name}: {message}",
                )
                return destination_sdk_pb2.MigrateResponse(
                    success=False,
                    warning=common_pb2.Warning(message=message),
                )

            # 1. Add the new column with the specified type.
            sql_bag.add(f"""
            ALTER TABLE "{schema}"."{table}" ADD COLUMN "{column_name}" {column_type};
            """)

            # Compute lists of columns.
            table_obj_tmp = deepcopy(table_obj)
            TableMetadataHelper.remove_column_from_table(table_obj_tmp, column_name)
            TableMetadataHelper.remove_column_from_table(
                table_obj_tmp, FieldMap.to_fivetran(FIVETRAN_START)
            )
            unchanged_columns = [
                f'"{FieldMap.to_cratedb(col.name)}"' for col in table_obj_tmp.columns
            ]
            all_columns = [*unchanged_columns, column_name, FIVETRAN_START]

            # 2. Insert new rows to record the history of the DDL operation.
            sql_bag.add(
                SqlStatement(
                    f"""
            INSERT INTO "{schema}"."{table}" ({", ".join(all_columns)})
            (
              SELECT
                {", ".join(unchanged_columns)},
                CAST(:default_value AS {column_type}) AS "{column_name}",
                CAST(:operation_timestamp AS TIMESTAMP) AS {FIVETRAN_START}
              FROM "{schema}"."{table}"
              WHERE {FIVETRAN_ACTIVE} = TRUE
                AND {FIVETRAN_START} < CAST(:operation_timestamp AS TIMESTAMP)
            );
            """,
                    {"default_value": default_value, "operation_timestamp": operation_timestamp},
                )
            )

            # 3. Update the newly added rows with the `default_value` and `operation_timestamp`.
            # This step is important in case of source connector sends multiple ADD_COLUMN_IN_HISTORY_MODE
            # operations with the same operation_timestamp. It will ensure, we only record history once
            # for that timestamp.
            sql_bag.add(
                SqlStatement(
                    f"""
            UPDATE "{schema}"."{table}"
            SET "{column_name}" = CAST(:default_value AS {column_type})
            WHERE {FIVETRAN_START} = CAST(:operation_timestamp AS TIMESTAMP)
            """,
                    {"default_value": default_value, "operation_timestamp": operation_timestamp},
                )
            )

            # 4. Update the previous active record's `_fivetran_end` to `(operation timestamp) - 1ms`
            #    and set `_fivetran_active` to `FALSE`.
            # Deactivate original active records (those without the new column set),
            # by updating the previous active record's `_fivetran_end` to
            # `(operation timestamp) - 1ms` and set `_fivetran_active` to `FALSE`.
            sql_bag.add(
                SqlStatement(
                    f"""
            UPDATE "{schema}"."{table}"
            SET {FIVETRAN_END} = CAST(:operation_timestamp AS TIMESTAMP) - INTERVAL '1 millisecond',
                {FIVETRAN_ACTIVE} = FALSE
            WHERE {FIVETRAN_ACTIVE} = TRUE
              AND {FIVETRAN_START} < CAST(:operation_timestamp AS TIMESTAMP);
            """,
                    {"operation_timestamp": operation_timestamp},
                )
            )
            with self.engine.connect() as conn:
                sql_bag.execute(conn)

            log_message(
                LOG_INFO,
                f"[Migrate:AddColumnHistory] table={schema}.{table} column={add_col_history_mode.column} type={add_col_history_mode.column_type} default={add_col_history_mode.default_value} op_ts={add_col_history_mode.operation_timestamp}",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        # Add a new column with a specified data type and default value.
        if entity_case == "add_column_with_default_value":
            """
            This migration should add a new column with the specified column type and default value.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#add_column_with_default_value
            """
            add_col_default_with_value = add_op.add_column_with_default_value

            new_col = table_obj.columns.add()
            new_col.name = add_col_default_with_value.column
            new_col.type = add_col_default_with_value.column_type
            default_value = add_col_default_with_value.default_value
            type_ = TypeMap.to_cratedb(new_col.type, new_col.params)

            # CrateDB does not implement `ALTER TABLE ... ADD COLUMN ... DEFAULT`,
            # so let's run two separate commands.
            # - https://github.com/crate/crate/issues/18783
            # - https://github.com/crate/cratedb-fivetran-destination/issues/111
            with self.engine.connect() as conn:
                # 1. Add the column without a default value.
                conn.execute(
                    sa.text(
                        f'ALTER TABLE "{schema}"."{table}" ADD COLUMN "{new_col.name}" {type_};'
                    )
                )
                # 2. Update the column with the default value.
                if default_value is not None:
                    conn.execute(
                        sa.text(
                            f'UPDATE "{schema}"."{table}" SET "{new_col.name}" = :default_value;'
                        ),
                        parameters={"default_value": default_value},
                    )

            log_message(
                LOG_INFO,
                f"[Migrate:AddColumnDefault] table={schema}.{table} column={add_col_default_with_value.column} type={add_col_default_with_value.column_type} default={add_col_default_with_value.default_value}",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        log_message(LOG_WARNING, "[Migrate:Add] No add entity specified")
        return destination_sdk_pb2.MigrateResponse(unsupported=True)

    def handle_update_column_value(self, upd, schema, table):
        """
        Handles update column value operation.
        https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#update_column_value_operation
        """
        with self.engine.connect() as conn:
            conn.execute(
                sa.text(f'UPDATE "{schema}"."{table}" SET "{upd.column}"=:value;'),
                parameters={"value": upd.value},
            )
            conn.execute(sa.text(f'REFRESH TABLE "{schema}"."{table}";'))

        log_message(
            LOG_INFO,
            f"[Migrate:UpdateColumnValue] table={schema}.{table} column={upd.column}",
        )
        return destination_sdk_pb2.MigrateResponse(success=True)

    def handle_table_sync_mode_migration(self, op, schema, table):
        """Handles table sync mode migration operations."""

        soft_deleted_column = (
            FieldMap.to_cratedb(op.soft_deleted_column)
            if op.HasField("soft_deleted_column")
            else None
        )

        # Determine the migration type and handle accordingly
        if op.type == destination_sdk_pb2.TableSyncModeMigrationType.SOFT_DELETE_TO_LIVE:
            """
            This migration converts a table from soft-delete mode to live mode.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#soft_delete_to_live
            """
            column_names = self.schema_helper.get_column_names(schema, table)
            with self.engine.connect() as conn:
                if soft_deleted_column in column_names:
                    # 1. Drop records where `soft_deleted_column`, from the migration request, is true.
                    conn.execute(
                        sa.text(f"""
                    DELETE FROM "{schema}"."{table}"
                    WHERE "{soft_deleted_column}" = TRUE
                    """)
                    )

                    # 2. If soft_deleted_column = _fivetran_deleted column, then drop it.
                    if soft_deleted_column == FIVETRAN_DELETED:
                        self.schema_helper.remove_soft_delete_column(
                            schema, table, FIVETRAN_DELETED
                        )
            log_message(
                LOG_INFO,
                f"[Migrate:TableSyncModeMigration] Migrating table={schema}.{table} from SOFT_DELETE to LIVE",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        if op.type == destination_sdk_pb2.TableSyncModeMigrationType.SOFT_DELETE_TO_HISTORY:
            """
            This migration converts a table from SOFT DELETE to HISTORY mode.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#soft_delete_to_history
            """

            self._table_soft_delete_to_history(schema, table, soft_deleted_column)

            log_message(
                LOG_INFO,
                f"[Migrate:TableSyncModeMigration] Migrating table={schema}.{table} from SOFT_DELETE to HISTORY",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        if op.type == destination_sdk_pb2.TableSyncModeMigrationType.HISTORY_TO_SOFT_DELETE:
            """
            This migration converts a table from HISTORY mode to SOFT DELETE mode.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#history_to_soft_delete
            """

            # Prologue: Set table read-only.
            temptable_name = table + "_history_to_soft_delete_tmp"
            with self._table_read_only(schema, table, temptable_name):
                # Retrieve primary key constraints from original table.
                primary_keys = self.schema_helper.get_primary_key_names(schema, table)

                # 1. Drop the primary key constraint if it exists.
                #    CrateDB can't drop PK constraints,
                #    so it needs to copy the table to a temporary table.
                self._table_copy_schema(schema, table, temptable_name, drop_pk_constraints=True)
                self._table_copy_data(schema, table, temptable_name)

                # 2. If _fivetran_deleted doesn't exist, then add it.
                if soft_deleted_column:
                    self.schema_helper.add_soft_delete_column(
                        schema, temptable_name, soft_deleted_column
                    )

                with self.engine.connect() as conn:
                    # 3. Delete history for all records (delete all versions of each
                    #    unique PK except the latest version).
                    # FIXME: How to implement this with CrateDB?
                    #        SQLParseException[line 3:17: mismatched input 'USING' expecting {<EOF>, ';'}]
                    '''
                    pk_names = [f'"{name}"' for name in primary_keys]
                    where_constraints = []
                    for pk_name in pk_names:
                        where_constraints.append(f"main_table.{pk_name} = temp_alias.{pk_name}")
                    conn.execute(
                        sa.text(f"""
                    DELETE FROM "{schema}"."{temptable_name}" AS main_table
                    USING (
                        SELECT {", ".join(pk_names)}
                                MAX("{FIVETRAN_START}") AS "MAX_FIVETRAN_START"
                        FROM "{schema}"."{table}"
                        GROUP BY {", ".join(pk_names)}
                        ) as temp_alias
                    WHERE
                        ({" AND ".join(where_constraints)})
                    AND (
                        main_table."{FIVETRAN_START}" <> temp_alias."MAX_FIVETRAN_START"
                        OR main_table."{FIVETRAN_START}" IS NULL
                    );
                    """)
                    )
                    '''
                    # Implementation suggested by CodeRabbit.
                    #
                    # This approach avoids the `USING` clause entirely and should
                    # work well with CrateDB's SQL dialect.
                    #
                    # How it works:
                    # - The subquery groups by primary key columns and selects the
                    #   `MAX(__fivetran_start)` for each group (the latest version).
                    # - The outer `DELETE` removes all rows where the tuple
                    #   `(PK columns, __fivetran_start)` is **not** in that set of
                    #   latest versions.
                    # - This effectively keeps only the most recent row for each
                    #   unique PK combination.
                    #
                    pk_names = [f'"{name}"' for name in primary_keys]

                    if pk_names:
                        # Build the column list for the tuple comparison.
                        tuple_columns = ", ".join(pk_names) + f', "{FIVETRAN_START}"'
                        group_by_columns = ", ".join(pk_names)

                        conn.execute(
                            sa.text(f"""
                        DELETE FROM "{schema}"."{temptable_name}"
                        WHERE ({tuple_columns}) NOT IN (
                            SELECT {group_by_columns}, MAX("{FIVETRAN_START}")
                            FROM "{schema}"."{temptable_name}"
                            GROUP BY {group_by_columns}
                        )
                        """)
                        )

                    # 4. Update the soft_deleted_column column based on _fivetran_active.
                    if soft_deleted_column:
                        conn.execute(
                            sa.text(f"""
                        UPDATE "{schema}"."{temptable_name}"
                        SET "{soft_deleted_column}" = CASE
                                                      WHEN {FIVETRAN_ACTIVE} = TRUE THEN FALSE
                                                      ELSE TRUE
                                                      END;
                        """)
                        )

                    # 5. Drop the history mode columns.
                    self.schema_helper.remove_history_mode_columns(schema, temptable_name)

                    # 6. Recreate the primary key constraint if it was dropped in step 1.
                    #    Remark: Not possible with CrateDB, because primary key
                    #            constraints can only be created on empty tables.
                    """
                    ALTER TABLE <schema.table> ADD CONSTRAINT <primary_key_constraint> PRIMARY KEY (<columns>);
                    """

            log_message(
                LOG_INFO,
                f"[Migrate:TableSyncModeMigration] Migrating table={schema}.{table} from HISTORY to SOFT_DELETE",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        if op.type == destination_sdk_pb2.TableSyncModeMigrationType.HISTORY_TO_LIVE:
            """
            This migration converts a table from HISTORY to LIVE mode.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#history_to_live
            """

            # Prologue: Set table read-only.
            temptable_name = table + "_history_to_live_tmp"
            with self._table_read_only(schema, table, temptable_name):
                # 1. Drop the primary key constraint if it exists.
                #    CrateDB can't drop PK constraints,
                #    so it needs to copy the table to a temporary table.

                with self.engine.connect() as conn:
                    # Prologue: Copy table to temporary table.
                    self._table_copy_schema(schema, table, temptable_name, drop_pk_constraints=True)
                    self._table_copy_data(schema, table, temptable_name)

                    # 2. If keep_deleted_rows is FALSE, then drop rows which are not active (skip if keep_deleted_rows is TRUE).
                    if not op.keep_deleted_rows:
                        conn.execute(
                            sa.text(f"""
                        DELETE FROM "{schema}"."{temptable_name}"
                        WHERE "{FIVETRAN_ACTIVE}" = FALSE;
                        """)
                        )

                    # 3. Drop the history mode columns.
                    self.schema_helper.remove_history_mode_columns(schema, temptable_name)

                    # 4. Recreate the primary key constraint if it was dropped in step 1.
                    #    Remark: Not possible with CrateDB, because primary key
                    #            constraints can only be created on empty tables.
                    """
                    ALTER TABLE "{schema}"."{table}" ADD CONSTRAINT pk PRIMARY KEY ("{FIVETRAN_START}");
                    """

            log_message(
                LOG_INFO,
                f"[Migrate:TableSyncModeMigration] Migrating table={schema}.{table} from HISTORY to LIVE",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        if op.type == destination_sdk_pb2.TableSyncModeMigrationType.LIVE_TO_SOFT_DELETE:
            """
            This migration converts a table from live mode to soft-delete mode.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#live_to_soft_delete
            """
            if not soft_deleted_column:
                return destination_sdk_pb2.MigrateResponse(
                    unsupported=True,
                    warning=common_pb2.Warning("`soft_deleted_column` must be set"),
                )
            with self.engine.connect() as conn:
                # 1. Add the `soft_deleted_column` column if it does not exist.
                self.schema_helper.add_soft_delete_column(schema, table, soft_deleted_column)

                # 2. Update `soft_deleted_column`.
                conn.execute(
                    sa.text(
                        f'''
                        UPDATE "{schema}"."{table}"
                        SET "{soft_deleted_column}" = FALSE
                        WHERE "{soft_deleted_column}" IS NULL
                        '''
                    )
                )

            log_message(
                LOG_INFO,
                f"[Migrate:TableSyncModeMigration] Migrating table={schema}.{table} from LIVE to SOFT_DELETE",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        if op.type == destination_sdk_pb2.TableSyncModeMigrationType.LIVE_TO_HISTORY:
            """
            This migration converts a table from live mode to history mode.
            https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#live_to_history
            """

            self._table_live_to_history(schema, table)

            log_message(
                LOG_INFO,
                f"[Migrate:TableSyncModeMigration] Migrating table={schema}.{table} from LIVE to HISTORY",
            )
            return destination_sdk_pb2.MigrateResponse(success=True)

        log_message(
            LOG_WARNING,
            f"[Migrate:TableSyncModeMigration] Unknown migration type for table={schema}.{table}",
        )  # pragma: no cover
        return destination_sdk_pb2.MigrateResponse(unsupported=True)  # pragma: no cover

    def _table_live_to_history(self, schema: str, table: str):
        """
        Convert table from live to history mode.
        https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#live_to_history

        Because CrateDB does not support updating primary keys,
        the following procedure copies the table into a temporary
        table.
        """

        # Prologue: Set table read-only.
        temptable_name = table + "_live_to_history_tmp"
        with self._table_read_only(schema, table, temptable_name):
            with self.engine.connect() as conn:
                # Copy table to temporary table.
                self._table_copy_schema(schema, table, temptable_name, drop_pk_constraints=True)
                self._table_copy_data(schema, table, temptable_name)

                # 1. Add the history mode columns to the table.
                self.schema_helper.add_history_mode_columns(schema, temptable_name)

                # 2. Set all the records as active and set the _fivetran_start, _fivetran_end,
                #    and _fivetran_active columns appropriately.
                conn.execute(
                    sa.text(f'''
                    UPDATE
                        "{schema}"."{temptable_name}"
                    SET
                        "{FIVETRAN_START}" = NOW(),
                        "{FIVETRAN_END}" = CAST(:max_timestamp AS TIMESTAMP),
                        "{FIVETRAN_ACTIVE}" = TRUE;
                    '''),
                    {"max_timestamp": MAX_TIMESTAMP},
                )

    def _table_soft_delete_to_history(self, schema: str, table: str, soft_deleted_column: str):
        """
        Convert table from SOFT DELETE to HISTORY mode.
        https://github.com/fivetran/fivetran_partner_sdk/blob/main/schema-migration-helper-service.md#soft_delete_to_history
        """

        # Prologue: Set table read-only.
        temptable_name = table + "_soft_delete_to_history_tmp"
        with self._table_read_only(schema, table, temptable_name):
            # Prologue: Copy table to temporary table.
            self._table_copy_schema(schema, table, temptable_name)
            self._table_copy_data(schema, table, temptable_name)

            # 1. Add the history mode columns to the table.
            self.schema_helper.add_history_mode_columns(schema, temptable_name)

            with self.engine.connect() as conn:
                # 2. Use soft_deleted_column to identify active records and set the values of
                #    _fivetran_start, _fivetran_end, and _fivetran_active columns appropriately.
                conn.execute(
                    sa.text(f"""
                UPDATE "{schema}"."{temptable_name}"
                SET
                    {FIVETRAN_ACTIVE} = CASE
                                        WHEN "{soft_deleted_column}" = TRUE THEN FALSE
                                        ELSE TRUE
                                        END,
                    {FIVETRAN_START}  = CASE
                                        WHEN "{soft_deleted_column}" = TRUE THEN CAST(:min_timestamp AS TIMESTAMP)
                                        ELSE (SELECT MAX({FIVETRAN_SYNCED}) FROM "{schema}"."{temptable_name}")
                                        END,
                    {FIVETRAN_END}    = CASE
                                        WHEN "{soft_deleted_column}" = TRUE THEN CAST(:min_timestamp AS TIMESTAMP)
                                        ELSE CAST(:max_timestamp AS TIMESTAMP)
                                        END
                """),
                    {"min_timestamp": MIN_TIMESTAMP, "max_timestamp": MAX_TIMESTAMP},
                )

                # 3. If soft_deleted_column = _fivetran_deleted, then drop it.
                if soft_deleted_column == FIVETRAN_DELETED:
                    self.schema_helper.remove_soft_delete_column(
                        schema, temptable_name, FIVETRAN_DELETED
                    )

    def _validate_history_table(self, schema, table, operation_timestamp):
        """
        Validate table is non-empty and `max(_fivetran_start) < operation_timestamp`.
        """
        with self.engine.connect() as conn:
            # Synchronize previous writes.
            conn.execute(sa.text(f'REFRESH TABLE "{schema}"."{table}";'))

            # Check for emptiness.
            cardinality = int(
                conn.execute(sa.text(f'SELECT COUNT(*) FROM "{schema}"."{table}";')).scalar_one()
            )
            if cardinality == 0:
                raise ValueError("table is empty")

            # Validate operation timestamp condition.
            sql = f"""
            SELECT TO_CHAR(MAX({FIVETRAN_START}), 'YYYY-MM-DDTHH:MI:SSZ') AS max_start
            FROM "{schema}"."{table}"
            WHERE {FIVETRAN_ACTIVE} = TRUE
            """
            max_start = conn.execute(sa.text(sql)).scalar_one()
            if max_start is not None and max_start >= operation_timestamp:
                raise ValueError(
                    f"`operation_timestamp` {operation_timestamp} must be after `max(_fivetran_start)` {max_start}"
                )

    def _table_copy_schema(
        self,
        schema: str,
        source_tablename: str,
        target_tablename: str,
        drop_pk_constraints: bool = False,
    ) -> sa.Table:
        with self.engine.connect() as conn:
            conn.execute(sa.text(f'DROP TABLE IF EXISTS "{schema}"."{target_tablename}"'))
            metadata = sa.MetaData(schema=schema)
            source_table = sa.Table(source_tablename, metadata, autoload_with=conn)
            target_table = sa.Table(target_tablename, metadata)
            for col in source_table.columns:
                target_table.append_column(
                    sa.Column(
                        name=col.name,
                        type_=col.type,
                        primary_key=col.primary_key and not drop_pk_constraints,
                        nullable=col.nullable and not col.primary_key,
                        default=col.default,
                        server_default=col.server_default,
                    )
                )
            metadata.create_all(conn, [target_table])
            conn.commit()
            return target_table

    def _table_copy_data(self, schema: str, source_tablename: str, target_tablename: str):
        with self.engine.connect() as conn:
            column_names = [
                f'"{colname}"'
                for colname in self.schema_helper.get_column_names(schema, source_tablename)
            ]
            conn.execute(
                sa.text(
                    f"""
            INSERT INTO "{schema}"."{target_tablename}" ({", ".join(column_names)})
            (
              SELECT
                {", ".join(column_names)}
              FROM "{schema}"."{source_tablename}"
            );
            """
                )
            )

    @contextlib.contextmanager
    def _table_read_only(self, schema: str, table: str, temptable: str):
        with self.engine.connect() as conn:
            conn.execute(
                sa.text(f"""ALTER TABLE "{schema}"."{table}" SET ("blocks.write"=true);""")
            )
            try:
                # Invoke wrapped workhorse code block.
                yield

                # Epilogue: Activate temporary table.
                self._table_read_write(schema, table)
                conn.execute(
                    sa.text(f"""
                ALTER CLUSTER SWAP TABLE "{schema}"."{temptable}" TO "{schema}"."{table}" WITH (drop_source=true)
                """)
                )
            finally:
                # Ensure writes are re-enabled even if migration fails mid-way.
                self._table_read_write(schema, table)

    def _table_read_write(self, schema: str, table: str):
        with self.engine.connect() as conn:
            conn.execute(sa.text(f"""ALTER TABLE "{schema}"."{table}" RESET ("blocks.write");"""))


class TableSchemaHelper:
    """Helper class for table schema operations"""

    def __init__(self, engine: sa.Engine):
        self.engine = engine

    def get_column_names(self, schema: str, table: str) -> t.List[str]:
        with self.engine.connect() as conn:
            inspector = sa.inspect(conn)
            columns = inspector.get_columns(table_name=table, schema=schema)
            return [col["name"] for col in columns]

    def get_primary_key_names(self, schema: str, table: str) -> t.List[str]:
        with self.engine.connect() as conn:
            metadata = sa.MetaData(schema=schema)
            pk_columns = sa.Table(table, metadata, autoload_with=conn).primary_key.columns
            return [col.name for col in pk_columns]

    def add_soft_delete_column(self, schema: str, table: str, column_name: str):
        """Adds a soft delete column to a table."""
        if not column_name:
            raise ValueError("`column_name` cannot be empty")
        column_names = self.get_column_names(schema, table)
        if column_name not in column_names:
            with self.engine.connect() as conn:
                conn.execute(
                    sa.text(
                        f'ALTER TABLE "{schema}"."{table}" ADD COLUMN "{column_name}" BOOLEAN DEFAULT FALSE'
                    )
                )
                # CrateDB backfill workaround.
                conn.execute(sa.text(f'UPDATE "{schema}"."{table}" SET "{column_name}"=FALSE'))

    def remove_soft_delete_column(self, schema: str, table: str, column_name: str):
        """Remove a soft delete column from a table."""
        with self.engine.connect() as conn:
            conn.execute(
                sa.text(f'ALTER TABLE "{schema}"."{table}" DROP COLUMN IF EXISTS "{column_name}"')
            )

    def add_history_mode_columns(self, schema: str, table: str):
        """Adds history mode columns to a table."""
        column_names = self.get_column_names(schema, table)

        sql_bag = SqlBag()

        if FIVETRAN_START not in column_names:
            sql_bag.add(f'''
            ALTER TABLE "{schema}"."{table}"
            ADD COLUMN "{FIVETRAN_START}" TIMESTAMP''')
        if FIVETRAN_END not in column_names:
            sql_bag.add(f'''
            ALTER TABLE "{schema}"."{table}"
            ADD COLUMN "{FIVETRAN_END}" TIMESTAMP''')
        if FIVETRAN_ACTIVE not in column_names:
            sql_bag.add(f'''
            ALTER TABLE "{schema}"."{table}"
            ADD COLUMN "{FIVETRAN_ACTIVE}" BOOLEAN DEFAULT TRUE''')
            # CrateDB backfill workaround.
            sql_bag.add(f'''
            UPDATE "{schema}"."{table}"
            SET "{FIVETRAN_ACTIVE}"=TRUE
            ''')

        with self.engine.connect() as conn:
            sql_bag.execute(conn)

    def remove_history_mode_columns(self, schema: str, table: str):
        """Removes history mode columns from a table."""
        sql_bag = SqlBag()

        # Note: `DROP COLUMN "{FIVETRAN_START}"` will only work when it's
        # not part of the primary key. This is currently implemented by
        # using a table copy operation that drops the pk constraint.
        sql_bag.add(f"""
        ALTER TABLE "{schema}"."{table}"
        DROP COLUMN "{FIVETRAN_START}",
        DROP COLUMN "{FIVETRAN_END}",
        DROP COLUMN "{FIVETRAN_ACTIVE}";
        """)

        with self.engine.connect() as conn:
            sql_bag.execute(conn)


class TableMetadataHelper:
    """Helper class for table metadata operations"""

    @staticmethod
    def remove_column_from_table(table_obj, column_name):
        """Removes a column from a table."""
        if not column_name or not hasattr(table_obj, "columns"):
            return
        # Create a new list of columns excluding the specified column
        columns_to_keep = [col for col in table_obj.columns if col.name != column_name]
        # Clear and repopulate
        del table_obj.columns[:]
        table_obj.columns.extend(columns_to_keep)

    @classmethod
    def column_lists(
        cls, table_obj: common_pb2.Table, modulo_column_name: t.Optional[str] = None
    ) -> t.Tuple[t.List[str], t.List[str]]:
        """Return list of column names."""
        table_obj_tmp = deepcopy(table_obj)
        if modulo_column_name is not None:
            TableMetadataHelper.remove_column_from_table(table_obj_tmp, modulo_column_name)
        TableMetadataHelper.remove_column_from_table(
            table_obj_tmp, FieldMap.to_fivetran(FIVETRAN_START)
        )
        unchanged_columns = [f'"{FieldMap.to_cratedb(col.name)}"' for col in table_obj_tmp.columns]
        if modulo_column_name is not None:
            all_columns = [*unchanged_columns, f'"{modulo_column_name}"', FIVETRAN_START]
        else:
            all_columns = [*unchanged_columns, FIVETRAN_START]
        return all_columns, unchanged_columns
