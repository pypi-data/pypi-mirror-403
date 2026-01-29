# ruff: noqa: S608  # Possible SQL injection vector through string-based query construction
# Source: https://github.com/fivetran/fivetran_sdk/tree/v2/examples/destination_connector/python
import logging
import typing as t
from concurrent import futures

import grpc
import sqlalchemy as sa

from cratedb_fivetran_destination.engine import (
    AlterTableInplaceStatements,
    AlterTableRecreateStatements,
    WriteBatchProcessor,
    WriteHistoryBatchProcessor,
)
from cratedb_fivetran_destination.model import (
    CrateDBKnowledge,
    FieldMap,
    FivetranKnowledge,
    FivetranTable,
    TableAddress,
    TableInfo,
    TypeMap,
)
from cratedb_fivetran_destination.util import LOG_INFO, LOG_WARNING, log_message
from fivetran_sdk import common_pb2, destination_sdk_pb2, destination_sdk_pb2_grpc

from . import read_csv
from .schema_migration_helper import SchemaMigrationHelper

logger = logging.getLogger()


class CrateDBDestinationImpl(destination_sdk_pb2_grpc.DestinationConnectorServicer):
    def __init__(self):
        self.metadata = sa.MetaData()
        self.engine: sa.Engine = None

    def ConfigurationForm(self, request, context):
        log_message(LOG_INFO, "Fetching configuration form")

        # Create the form fields.
        form_fields = common_pb2.ConfigurationFormResponse(
            schema_selection_supported=True, table_selection_supported=True
        )

        # SQLAlchemy database connection URL.
        url = common_pb2.FormField(
            name="url",
            label="CrateDB database connection URL in SQLAlchemy format",
            text_field=common_pb2.TextField.PlainText,
            placeholder="crate://<username>:<password>@example.gke1.us-central1.gcp.cratedb.net:4200?ssl=true",
            default_value="crate://",
        )

        # Add fields to the form.
        form_fields.fields.append(url)

        # Add tests to the form.
        form_fields.tests.add(name="connect", label="Tests connection")
        # TODO: How to invoke this test?
        form_fields.tests.add(name="select", label="Tests selection")

        return form_fields

    def Test(self, request, context):
        """
        Verify database connectivity with configured connection parameters.
        """
        log_message(LOG_INFO, f"Test database connection: {request.name}")
        self._configure_database(request.configuration.get("url"))
        with self.engine.connect() as connection:
            connection.execute(sa.text("SELECT 42"))
        return common_pb2.TestResponse(success=True)

    def CreateTable(self, request, context):
        """
        Create database table using SQLAlchemy.
        """
        self._configure_database(request.configuration.get("url"))
        logger.info(
            "[CreateTable] :"
            + str(request.schema_name)
            + " | "
            + str(request.table.name)
            + " | "
            + str(request.table.columns)
        )
        self._create_table(
            schema_name=request.schema_name,
            table_name=request.table.name,
            fivetran_columns=request.table.columns,
        )
        return destination_sdk_pb2.CreateTableResponse(success=True)

    def AlterTable(self, request, context):
        """
        Alter schema of database table.
        """
        self._configure_database(request.configuration.get("url"))
        res: destination_sdk_pb2.AlterTableResponse  # noqa: F842
        logger.info(
            "[AlterTable]: "
            + str(request.schema_name)
            + " | "
            + str(request.table.name)
            + " | "
            + str(request.table.columns)
        )

        # Compute schema diff.
        old_table = self.DescribeTable(request, context).table
        new_table = request.table

        pk_has_changed = False
        if not FivetranTable.pk_equals(old_table, new_table):
            pk_has_changed = True

        columns_old: t.Dict[str, common_pb2.Column] = {
            column.name: column for column in old_table.columns
        }

        columns_new: t.List[common_pb2.Column] = []
        columns_changed: t.List[common_pb2.Column] = []
        columns_common: t.List[common_pb2.Column] = []
        columns_deleted: t.List[common_pb2.Column] = []

        for column in new_table.columns:
            column_old = columns_old.get(column.name)
            if column_old is None:
                columns_new.append(column)
            else:
                columns_common.append(column)
                type_old = TypeMap.to_cratedb(column_old.type, column_old.params)
                type_new = TypeMap.to_cratedb(column.type, column.params)
                if type_old != type_new:
                    if column_old.primary_key:
                        pk_has_changed = True
                        continue

                    columns_changed.append(column)

        table_info = self._table_info_from_request(request)

        if request.drop_columns:
            new_column_names = [column.name for column in new_table.columns]
            for column in old_table.columns:
                if column.name not in new_column_names:
                    columns_deleted.append(column)
            if columns_deleted:
                amendments = []
                for column in columns_deleted:
                    amendments.append(f'DROP COLUMN "{column.name}"')
                with self.engine.connect() as connection:
                    connection.execute(
                        sa.text(f"ALTER TABLE {table_info.fullname} {', '.join(amendments)}")
                    )
                log_message(
                    LOG_INFO, f"AlterTable: Successfully altered table: {table_info.fullname}"
                )
            else:
                log_message(LOG_INFO, "AlterTable (drop columns): Nothing changed")
            return destination_sdk_pb2.AlterTableResponse(success=True)

        if pk_has_changed:
            log_message(
                LOG_WARNING,
                "Alter table intends to change the primary key of the table. "
                "Because CrateDB does not support this operation, the table will be recreated.",
            )

            # TODO: Refactor this _into_ the `AlterTableRecreateStatements` workhorse function.
            temptable = request.table.name + "_alter_tmp"
            self._drop_table(
                schema_name=request.schema_name,
                table_name=temptable,
            )
            self._create_table(
                schema_name=request.schema_name,
                table_name=temptable,
                fivetran_columns=request.table.columns,
            )
            ats = AlterTableRecreateStatements(
                address_effective=TableAddress(
                    schema_name=request.schema_name, table_name=request.table.name
                ),
                address_temporary=TableAddress(
                    schema_name=request.schema_name, table_name=temptable
                ),
                columns_old=old_table.columns,
                columns_new=new_table.columns,
            ).to_sql()
        else:
            ats = AlterTableInplaceStatements(
                table=table_info, columns_new=columns_new, columns_changed=columns_changed
            ).to_sql()
        if ats:
            with self.engine.connect() as connection:
                ats.execute(connection)
                log_message(
                    LOG_INFO, f"AlterTable: Successfully altered table: {table_info.fullname}"
                )
        else:
            log_message(LOG_INFO, "AlterTable: Nothing changed")

        return destination_sdk_pb2.AlterTableResponse(success=True)

    def Truncate(self, request, context):
        """
        Truncate database table.
        """
        self._configure_database(request.configuration.get("url"))
        logger.info(
            "[TruncateTable]: "
            + str(request.schema_name)
            + " | "
            + str(request.table_name)
            + " | soft"
            + str(request.soft)
        )
        with self.engine.connect() as connection:
            connection.execute(sa.text(f"DELETE FROM {self.table_fullname(request)}"))
        return destination_sdk_pb2.TruncateResponse(success=True)

    def WriteBatch(self, request, context):
        """
        Load data into table.
        """
        self._configure_database(request.configuration.get("url"))
        table_info = self._table_info_from_request(request)
        log_message(LOG_INFO, f"Data loading started for table: {request.table.name}")
        processor = WriteBatchProcessor(self.engine)
        processor.process(
            table_info=table_info,
            upsert_records=self._files_to_records(request, request.replace_files),
            update_records=self._files_to_records(request, request.update_files),
            delete_records=self._files_to_records(request, request.delete_files),
        )
        log_message(LOG_INFO, f"Data loading completed for table: {request.table.name}")

        res: destination_sdk_pb2.WriteBatchResponse = destination_sdk_pb2.WriteBatchResponse(
            success=True
        )
        return res

    def WriteHistoryBatch(self, request, context):
        """
        Load data into table under history mode.
        History mode allows to capture every available version of each record.
        """
        self._configure_database(request.configuration.get("url"))
        table_info = self._table_info_from_request(request)
        log_message(
            LOG_INFO, f"Data loading in history mode started for table: {request.table.name}"
        )
        processor = WriteHistoryBatchProcessor(engine=self.engine)
        processor.process(
            table_info=table_info,
            earliest_start_records=self._files_to_records(request, request.earliest_start_files),
            # TODO: Those operations are currently taken from regular table loading.
            #       Please verify if they need to be adjusted for history mode.
            update_records=self._files_to_records(request, request.update_files),
            replace_records=self._files_to_records(request, request.replace_files),
            delete_records=self._files_to_records(request, request.delete_files),
        )
        log_message(
            LOG_INFO, f"Data loading in history mode completed for table: {request.table.name}"
        )

        res: destination_sdk_pb2.WriteBatchResponse = destination_sdk_pb2.WriteBatchResponse(
            success=True
        )
        return res

    def DescribeTable(self, request, context):
        """
        Reflect table schema using SQLAlchemy.
        """
        self._configure_database(request.configuration.get("url"))
        table_name = self.table_name(request)
        schema_name = self.schema_name(request)
        table: common_pb2.Table = common_pb2.Table(name=table_name)
        try:
            sa_table = self._reflect_table(schema=schema_name, table=table_name)
        except sa.exc.NoSuchTableError:
            msg = f"Table not found: {table_name}"
            log_message(LOG_WARNING, f"DescribeTable: {msg}")
            return destination_sdk_pb2.DescribeTableResponse(
                not_found=True, table=table, warning=common_pb2.Warning(message=msg)
            )
        sa_column: sa.Column
        for sa_column in sa_table.columns:
            ft_column = common_pb2.Column(
                name=FieldMap.to_fivetran(sa_column.name),
                type=TypeMap.to_fivetran(sa_column.type),
                primary_key=sa_column.primary_key,
            )
            table.columns.append(ft_column)
        log_message(LOG_INFO, f"Completed fetching table info: {table}")
        return destination_sdk_pb2.DescribeTableResponse(not_found=False, table=table)

    def Migrate(self, request, context):
        """
        Implementation of the new Migrate RPC introduced for schema migration support.

        :param request: The migration request contains details of the operation.
        :param context: gRPC context
        """
        self._configure_database(request.configuration.get("url"))
        migration_helper = SchemaMigrationHelper(self.engine)

        details = request.details
        schema = details.schema
        table = details.table

        operation_case = details.WhichOneof("operation")
        log_message(LOG_INFO, f"[Migrate] schema={schema} table={table} operation={operation_case}")

        table_obj = self.DescribeTable(request, context).table

        if operation_case == "drop":
            response = migration_helper.handle_drop(details.drop, schema, table, table_obj)

        elif operation_case == "copy":
            response = migration_helper.handle_copy(details.copy, schema, table, table_obj)

        elif operation_case == "rename":
            response = migration_helper.handle_rename(details.rename, schema, table)

        elif operation_case == "add":
            response = migration_helper.handle_add(details.add, schema, table, table_obj)

        elif operation_case == "update_column_value":
            response = migration_helper.handle_update_column_value(
                details.update_column_value, schema, table
            )

        elif operation_case == "table_sync_mode_migration":
            response = migration_helper.handle_table_sync_mode_migration(
                details.table_sync_mode_migration, schema, table
            )

        else:
            log_message(LOG_WARNING, "[Migrate] Unsupported or missing operation")
            response = destination_sdk_pb2.MigrateResponse(unsupported=True)

        return response

    def _configure_database(self, url):
        if not self.engine:
            self.engine = sa.create_engine(url, echo=False)

    @staticmethod
    def _files_to_records(request, files: t.List[str]):
        """
        Decrypt payload files and generate records.
        """
        for filename in files:
            value = request.keys[filename]
            logger.info(f"Decrypting file: {filename}")
            for record in read_csv.decrypt_file(filename, value):
                # Rename keys according to field map.
                record = FieldMap.rename_keys(record)
                # Replace magic Fivetran values.
                FivetranKnowledge.replace_values(record)
                # Adjust values to data types for CrateDB.
                CrateDBKnowledge.replace_values(request, record)
                yield record

    def _reflect_table(self, schema: str, table: str):
        """
        Acquire table schema from database.
        """
        return sa.Table(
            table,
            sa.MetaData(),
            schema=schema,
            quote_schema=True,
            autoload_with=self.engine,
        )

    def _table_info_from_request(self, request) -> TableInfo:
        """
        Compute TableInfo data.
        """
        table = self._reflect_table(schema=request.schema_name, table=request.table.name)
        primary_keys = [column.name for column in table.primary_key.columns]
        return TableInfo(fullname=self.table_fullname(request), primary_keys=primary_keys)

    def _table_info_from_fivetran(self, table: common_pb2.Table) -> TableInfo:  # pragma: nocover
        """
        Compute TableInfo data.
        """
        primary_keys = [column.name for column in table.columns if column.primary_key]
        return TableInfo(fullname=table.name, primary_keys=primary_keys)

    @staticmethod
    def schema_name(request):
        """
        Return schema name from request object.
        """
        if hasattr(request, "details"):
            return request.details.schema
        return request.schema_name

    @staticmethod
    def table_name(request):
        """
        Return table name from request object.
        """
        if hasattr(request, "details"):
            return request.details.table
        if hasattr(request, "table"):
            return request.table.name
        return request.table_name

    def table_fullname(self, request):
        """
        Return full-qualified table name from request object.
        """
        table_name = self.table_name(request)
        return f'"{request.schema_name}"."{table_name}"'

    def _create_table(
        self, schema_name: str, table_name: str, fivetran_columns: t.List[common_pb2.Column]
    ) -> sa.Table:
        table = sa.Table(table_name, self.metadata, schema=schema_name)
        fivetran_column: common_pb2.Column
        for fivetran_column in fivetran_columns:
            name = FieldMap.to_cratedb(fivetran_column.name)
            type_ = TypeMap.to_cratedb(fivetran_column.type, fivetran_column.params)
            db_column = sa.Column(
                name,
                type_,
                primary_key=fivetran_column.primary_key,
                nullable=not fivetran_column.primary_key,
            )
            # TODO: Which kind of parameters are relayed by Fivetran here?
            # db_column.params(fivetran_column.params)  # noqa: ERA001
            table.append_column(db_column, replace_existing=True)

        table.create(self.engine)
        return table

    def _drop_table(self, schema_name: str, table_name: str, if_exists: bool = True) -> None:
        table = sa.Table(table_name, self.metadata, schema=schema_name)
        table.drop(self.engine, checkfirst=if_exists)


def start_server(host: str = "[::]", port: int = 50052, max_workers: int = 1) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    server.add_insecure_port(f"{host}:{port}")
    destination_sdk_pb2_grpc.add_DestinationConnectorServicer_to_server(
        CrateDBDestinationImpl(), server
    )
    server.start()
    return server
