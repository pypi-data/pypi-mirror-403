import pytest
import sqlalchemy as sa

from cratedb_fivetran_destination.engine import (
    AlterTableRecreateStatements,
    EarliestStartHistoryStatements,
)
from cratedb_fivetran_destination.model import TableAddress, TableInfo
from cratedb_fivetran_destination.schema_migration_helper import SchemaMigrationHelper
from fivetran_sdk import common_pb2


def test_earliest_start_history_statements():
    eshs = EarliestStartHistoryStatements(table=TableInfo("testdrive.foo"), records=[])
    assert eshs.hard_delete_with_timestamp() is None


def test_schema_migration_helper_validate_history_table(engine):
    smh = SchemaMigrationHelper(engine)

    # Create an empty table to trigger the error condition.
    with engine.connect() as conn:
        conn.execute(sa.text("CREATE TABLE testdrive.foo (id INT);"))

    # Run history table operation pre-flight checks.
    with pytest.raises(ValueError) as excinfo:
        smh._validate_history_table(
            schema="testdrive", table="foo", operation_timestamp="2005-05-23T20:57:00Z"
        )

    # Validate the assertion.
    assert excinfo.match("table is empty")


def test_alter_table_recreate_statements_column_count_mismatch():
    """
    Validate exception is raised when column counts do not match.
    """
    ats = AlterTableRecreateStatements(
        address_effective=TableAddress(schema_name="testdrive", table_name="foo"),
        address_temporary=TableAddress(schema_name="testdrive", table_name="foo_tmp"),
        columns_old=[common_pb2.Column(name="id", type=common_pb2.STRING)],
        columns_new=[
            common_pb2.Column(name="id", type=common_pb2.STRING),
            common_pb2.Column(name="name", type=common_pb2.STRING),
        ],
    )

    with pytest.raises(ValueError) as excinfo:
        ats.to_sql()
    assert excinfo.match("Column count mismatch")
