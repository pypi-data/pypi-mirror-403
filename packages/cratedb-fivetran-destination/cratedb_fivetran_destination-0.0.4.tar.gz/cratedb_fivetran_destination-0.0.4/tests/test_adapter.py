import re

import pytest
import sqlalchemy as sa

from cratedb_fivetran_destination import __version__
from cratedb_fivetran_destination.engine import WriteBatchProcessor
from cratedb_fivetran_destination.model import TableInfo
from cratedb_fivetran_destination.util import format_log_message, setup_logging
from fivetran_sdk import common_pb2, destination_sdk_pb2


def test_version():
    assert __version__ >= "0.0.0"


def test_setup_logging():
    setup_logging(verbose=True)


def test_api_test(capsys):
    """
    Invoke gRPC API method `Test`.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    destination = CrateDBDestinationImpl()

    # Invoke gRPC API method.
    config = {"url": "crate://"}
    response = destination.Test(
        request=common_pb2.TestRequest(name="foo", configuration=config),
        context=common_pb2.TestResponse(),
    )

    # Validate outcome.
    assert response.success is True
    assert response.failure == ""

    # Check log output.
    out, _ = capsys.readouterr()
    assert format_log_message("Test database connection: foo", newline=True) in out


def test_api_configuration_form(capsys):
    """
    Invoke gRPC API method `ConfigurationForm`.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    destination = CrateDBDestinationImpl()

    # Invoke gRPC API method.
    response = destination.ConfigurationForm(
        request=common_pb2.ConfigurationFormRequest(),
        context=common_pb2.ConfigurationFormResponse(),
    )

    # Extract field of concern.
    url_field: common_pb2.FormField = response.fields[0]

    # Validate fields.
    assert url_field.name == "url"
    assert "CrateDB database connection URL" in url_field.label

    # Validate tests.
    assert response.tests[0].name == "connect"

    # Check log output.
    out, _ = capsys.readouterr()
    assert out == format_log_message("Fetching configuration form", newline=True)


def test_api_describe_table_found(engine, capsys):
    """
    Invoke gRPC API method `DescribeTable` on an existing table.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    destination = CrateDBDestinationImpl()

    with engine.connect() as conn:
        conn.execute(sa.text("CREATE TABLE testdrive.foo (id INT)"))

    # Invoke gRPC API method under test.
    config = {"url": "crate://"}
    response = destination.DescribeTable(
        request=destination_sdk_pb2.DescribeTableRequest(
            table_name="foo", schema_name="testdrive", configuration=config
        ),
        context=destination_sdk_pb2.DescribeTableResponse(),
    )

    # Validate outcome.
    assert response.not_found is False
    assert response.warning.message == ""
    assert response.table == common_pb2.Table(
        name="foo",
        columns=[
            common_pb2.Column(
                name="id",
                type=common_pb2.DataType.INT,
                primary_key=False,
            )
        ],
    )

    # Check log output.
    out, _ = capsys.readouterr()
    assert "Completed fetching table info" in out


def test_api_describe_table_not_found(capsys):
    """
    Invoke gRPC API method `DescribeTable` on an existing table.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    destination = CrateDBDestinationImpl()

    # Invoke gRPC API method under test.
    config = {"url": "crate://"}
    response = destination.DescribeTable(
        request=destination_sdk_pb2.DescribeTableRequest(
            table_name="unknown", schema_name="testdrive", configuration=config
        ),
        context=destination_sdk_pb2.DescribeTableResponse(),
    )

    # Validate outcome.
    assert response.not_found is False
    assert response.warning.message == "Table not found: unknown"
    assert response.table.name == ""
    assert response.table.columns == []

    # Check log output.
    out, _ = capsys.readouterr()
    assert out == format_log_message(
        "DescribeTable: Table not found: unknown", level="WARNING", newline=True
    )


def test_api_alter_table_add_column(engine, capsys):
    """
    Invoke gRPC API method `AlterTable`, adding a new column.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    destination = CrateDBDestinationImpl()

    with engine.connect() as conn:
        conn.execute(sa.text("CREATE TABLE testdrive.foo (id INT)"))

    # Invoke gRPC API method under test.
    table: common_pb2.Table = common_pb2.Table(name="foo")
    column: common_pb2.Column = common_pb2.Column(
        name="bar",
        type=common_pb2.DataType.STRING,
        primary_key=False,
    )
    table.columns.append(column)
    config = {"url": "crate://"}
    response = destination.AlterTable(
        request=destination_sdk_pb2.AlterTableRequest(
            table=table, schema_name="testdrive", configuration=config
        ),
        context=destination_sdk_pb2.AlterTableResponse(),
    )

    # Validate outcome.
    assert response.success is True
    assert response.warning.message == ""

    # Check log output.
    out, _ = capsys.readouterr()
    assert (
        format_log_message(
            'AlterTable: Successfully altered table: "testdrive"."foo"', newline=True
        )
        in out
    )


def test_api_alter_table_nothing_changed(engine, capsys):
    """
    Invoke gRPC API method `AlterTable`, but nothing changed.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    destination = CrateDBDestinationImpl()

    with engine.connect() as conn:
        conn.execute(sa.text("CREATE TABLE testdrive.foo (id INT)"))

    # Invoke gRPC API method under test.
    table: common_pb2.Table = common_pb2.Table(
        name="foo",
        columns=[
            common_pb2.Column(
                name="id",
                type=common_pb2.DataType.INT,
                primary_key=False,
            )
        ],
    )
    config = {"url": "crate://"}
    response = destination.AlterTable(
        request=destination_sdk_pb2.AlterTableRequest(
            table=table, schema_name="testdrive", configuration=config
        ),
        context=destination_sdk_pb2.AlterTableResponse(),
    )

    # Validate outcome.
    assert response.success is True
    assert response.warning.message == ""

    # Check log output.
    out, _ = capsys.readouterr()
    assert format_log_message("AlterTable: Nothing changed", newline=True) in out


def test_api_alter_table_drop_column_nothing_changed(engine, capsys):
    """
    Invoke gRPC API method `AlterTable` with `drop_columns=True`, but nothing changed.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    destination = CrateDBDestinationImpl()

    with engine.connect() as conn:
        conn.execute(sa.text("CREATE TABLE testdrive.foo (id INT)"))

    # Invoke gRPC API method under test.
    table: common_pb2.Table = common_pb2.Table(
        name="foo",
        columns=[
            common_pb2.Column(
                name="id",
                type=common_pb2.DataType.INT,
                primary_key=False,
            )
        ],
    )
    config = {"url": "crate://"}
    response = destination.AlterTable(
        request=destination_sdk_pb2.AlterTableRequest(
            table=table, schema_name="testdrive", configuration=config, drop_columns=True
        ),
        context=destination_sdk_pb2.AlterTableResponse(),
    )

    # Validate outcome.
    assert response.success is True
    assert response.warning.message == ""

    # Check log output.
    out, _ = capsys.readouterr()
    assert format_log_message("AlterTable (drop columns): Nothing changed", newline=True) in out


def test_api_alter_table_change_primary_key_type(engine, capsys):
    """
    Invoke gRPC API method `AlterTable`, changing the type of the primary key.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    destination = CrateDBDestinationImpl()

    with engine.connect() as conn:
        conn.execute(sa.text("CREATE TABLE testdrive.foo (id INT PRIMARY KEY)"))

    # Invoke gRPC API method under test.
    table: common_pb2.Table = common_pb2.Table(name="foo")
    column: common_pb2.Column = common_pb2.Column(
        name="id",
        type=common_pb2.DataType.STRING,
        primary_key=True,
    )
    table.columns.append(column)
    config = {"url": "crate://"}
    response = destination.AlterTable(
        request=destination_sdk_pb2.AlterTableRequest(
            table=table, schema_name="testdrive", configuration=config
        ),
        context=destination_sdk_pb2.AlterTableResponse(),
    )

    # Validate outcome.
    assert response.success is True

    # Check log output.
    out, _ = capsys.readouterr()
    assert (
        format_log_message(
            'AlterTable: Successfully altered table: "testdrive"."foo"', newline=True
        )
        in out
    )


def test_api_alter_table_change_primary_key_name(engine, capsys):
    """
    Invoke gRPC API method `AlterTable`, changing the name of the primary key.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    destination = CrateDBDestinationImpl()

    with engine.connect() as conn:
        conn.execute(sa.text("CREATE TABLE testdrive.foo (id INT PRIMARY KEY)"))

    # Invoke gRPC API method under test.
    table: common_pb2.Table = common_pb2.Table(name="foo")
    column: common_pb2.Column = common_pb2.Column(
        name="identifier",
        type=common_pb2.DataType.INT,
        primary_key=True,
    )
    table.columns.append(column)
    config = {"url": "crate://"}
    response = destination.AlterTable(
        request=destination_sdk_pb2.AlterTableRequest(
            table=table, schema_name="testdrive", configuration=config
        ),
        context=destination_sdk_pb2.AlterTableResponse(),
    )

    # Validate outcome.
    assert response.success is True

    # Check log output.
    out, _ = capsys.readouterr()
    assert (
        format_log_message(
            'AlterTable: Successfully altered table: "testdrive"."foo"', newline=True
        )
        in out
    )


def migration_request(**migration_kwargs):
    """
    A shortcut utility function to create a gRPC MigrateRequest instance.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    # Invoke gRPC API method under test.
    config = {"url": "crate://"}
    destination = CrateDBDestinationImpl()
    return destination.Migrate(
        request=destination_sdk_pb2.MigrateRequest(
            configuration=config,
            details=destination_sdk_pb2.MigrationDetails(**migration_kwargs),
        ),
        context=destination_sdk_pb2.MigrateResponse(),
    )


def test_api_migrate_missing_operation(capsys):
    """
    Invoke gRPC `Migrate` without operation.
    """

    # Invoke gRPC API method under test.
    response = migration_request()

    # Validate outcome.
    assert response.success is False
    assert response.unsupported is True

    # Validate log output.
    out, _ = capsys.readouterr()
    assert "[Migrate] Unsupported or missing operation" in out


def test_api_migrate_add_without_entity(capsys):
    """
    Invoke `SchemaMigrationHelper::handle_add` without entity.
    """

    # Invoke gRPC API method under test.
    response = migration_request(add=destination_sdk_pb2.AddOperation())

    # Validate outcome.
    assert response.success is False
    assert response.unsupported is True

    # Validate log output.
    out, _ = capsys.readouterr()
    assert "[Migrate:Add] No add entity specified" in out


def test_api_migrate_copy_without_entity(capsys):
    """
    Invoke `SchemaMigrationHelper::handle_copy` without entity.
    """

    # Invoke gRPC API method under test.
    response = migration_request(copy=destination_sdk_pb2.CopyOperation())

    # Validate outcome.
    assert response.success is False
    assert response.unsupported is True

    # Validate log output.
    out, _ = capsys.readouterr()
    assert "[Migrate:Copy] No copy entity specified" in out


def test_api_migrate_drop_without_entity(capsys):
    """
    Invoke `SchemaMigrationHelper::handle_drop` without entity.
    """

    # Invoke gRPC API method under test.
    response = migration_request(drop=destination_sdk_pb2.DropOperation())

    # Validate outcome.
    assert response.success is False
    assert response.unsupported is True

    # Validate log output.
    out, _ = capsys.readouterr()
    assert "[Migrate:Drop] No drop entity specified" in out


def test_api_migrate_rename_without_entity(capsys):
    """
    Invoke `SchemaMigrationHelper::handle_rename` without entity.
    """

    # Invoke gRPC API method under test.
    response = migration_request(rename=destination_sdk_pb2.RenameOperation())

    # Validate outcome.
    assert response.success is False
    assert response.unsupported is True

    # Validate log output.
    out, _ = capsys.readouterr()
    assert "[Migrate:Rename] No rename entity specified" in out


def test_api_migrate_add_column_in_history_mode_operation_timestamp_wrong(engine):
    """
    Invoke gRPC `Migrate::add_column_in_history_mode` operation with wrong operation_timestamp.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    destination = CrateDBDestinationImpl()

    with engine.connect() as conn:
        conn.execute(
            sa.text("""
        CREATE TABLE testdrive.foo (
            id INT,
            "__fivetran_synced" TIMESTAMP WITHOUT TIME ZONE,
            "__fivetran_start" TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            "__fivetran_end" TIMESTAMP WITHOUT TIME ZONE,
            "__fivetran_active" BOOLEAN
        )
        """)
        )
        conn.execute(
            sa.text("""
        INSERT INTO testdrive.foo (id, __fivetran_start, __fivetran_active)
        VALUES (42, '2005-05-24T20:57:00Z', TRUE);
        """)
        )

    # Invoke gRPC API method under test.
    config = {"url": "crate://"}
    response = destination.Migrate(
        request=destination_sdk_pb2.MigrateRequest(
            configuration=config,
            details=destination_sdk_pb2.MigrationDetails(
                schema="testdrive",
                table="foo",
                add=destination_sdk_pb2.AddOperation(
                    add_column_in_history_mode=destination_sdk_pb2.AddColumnInHistoryMode(
                        column="data",
                        column_type=common_pb2.DataType.STRING,
                        default_value="foo",
                        operation_timestamp="2005-05-23T20:57:00Z",
                    ),
                ),
            ),
        ),
        context=destination_sdk_pb2.MigrateResponse(),
    )

    # Validate outcome.
    assert response.success is False
    pattern = "`operation_timestamp` .+ must be after `max\\(_fivetran_start\\)` .+"
    assert re.match(pattern, response.warning.message), (
        f"{response.warning.message} did not match pattern"
    )


def test_api_migrate_drop_column_in_history_mode_operation_timestamp_wrong(engine):
    """
    Invoke gRPC `Migrate::drop_column_in_history_mode` operation with wrong operation_timestamp.
    """
    from cratedb_fivetran_destination.main import CrateDBDestinationImpl

    destination = CrateDBDestinationImpl()

    with engine.connect() as conn:
        conn.execute(
            sa.text("""
        CREATE TABLE testdrive.foo (
            id INT,
            "__fivetran_synced" TIMESTAMP WITHOUT TIME ZONE,
            "__fivetran_start" TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            "__fivetran_end" TIMESTAMP WITHOUT TIME ZONE,
            "__fivetran_active" BOOLEAN
        )
        """)
        )
        conn.execute(
            sa.text("""
        INSERT INTO testdrive.foo (id, __fivetran_start, __fivetran_active)
        VALUES (42, '2005-05-24T20:57:00Z', TRUE);
        """)
        )

    # Invoke gRPC API method under test.
    config = {"url": "crate://"}
    response = destination.Migrate(
        request=destination_sdk_pb2.MigrateRequest(
            configuration=config,
            details=destination_sdk_pb2.MigrationDetails(
                schema="testdrive",
                table="foo",
                drop=destination_sdk_pb2.DropOperation(
                    drop_column_in_history_mode=destination_sdk_pb2.DropColumnInHistoryMode(
                        column="data",
                        operation_timestamp="2005-05-23T20:57:00Z",
                    ),
                ),
            ),
        ),
        context=destination_sdk_pb2.MigrateResponse(),
    )

    # Validate outcome.
    assert response.success is False
    pattern = "`operation_timestamp` .+ must be after `max\\(_fivetran_start\\)` .+"
    assert re.match(pattern, response.warning.message), (
        f"{response.warning.message} did not match pattern"
    )


def test_processor_failing(engine):
    table_info = TableInfo(fullname="unknown.unknown", primary_keys=["id"])
    p = WriteBatchProcessor(engine=engine)
    with pytest.raises(sa.exc.ProgrammingError) as ex:
        p.process(
            table_info=table_info,
            upsert_records=[{"id": 1, "name": "Hotzenplotz"}],
            update_records=[{"id": 2}],
            delete_records=[{"id": 2}],
        )
    assert ex.match(re.escape("SchemaUnknownException[Schema 'unknown' unknown]"))
