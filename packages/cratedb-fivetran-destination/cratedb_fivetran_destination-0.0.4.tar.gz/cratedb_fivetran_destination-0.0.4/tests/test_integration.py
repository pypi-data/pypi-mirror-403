import subprocess
import threading
from time import sleep
from unittest import mock

import pytest
import sqlalchemy as sa
from sqlalchemy.sql.type_api import UserDefinedType
from sqlalchemy.testing.util import drop_all_tables
from sqlalchemy_cratedb import ObjectType

from cratedb_fivetran_destination.testing import SDK_TESTER_OCI, get_sdk_tester_command
from tests.conftest import unblock_all_tables

pytestmark = pytest.mark.sdktester


def run(command, background: bool = False):
    if background:
        return subprocess.Popen(command, shell=True)  # noqa: S602
    subprocess.check_call(command, stderr=subprocess.STDOUT, shell=True)  # noqa: S602
    return None


@pytest.fixture(autouse=True)
def reset_tables(engine):
    with engine.connect() as connection:
        inspector = sa.inspect(connection)
        unblock_all_tables(engine, inspector, schema="tester")
        drop_all_tables(engine, inspector, schema="tester")


@pytest.fixture()
def services(request):
    """
    Invoke the CrateDB Fivetran destination gRPC adapter and the Fivetran destination tester.
    """
    data_folder = request.param

    processes = []

    oci_image = SDK_TESTER_OCI
    run("gcloud auth configure-docker us-docker.pkg.dev")
    run(f"docker pull {oci_image}")

    # Start gRPC server.
    from cratedb_fivetran_destination.main import start_server

    server = None

    def starter():
        nonlocal server
        server = start_server()

    t = threading.Thread(target=starter)
    t.start()

    cmd = get_sdk_tester_command(directory=data_folder)
    processes.append(run(cmd, background=True))
    sleep(10)

    yield

    # Terminate processes again.
    for proc in processes:
        proc.terminate()
        proc.wait(3)

    # Terminate gRPC server.
    server.stop(grace=3.0)


# The record that is inserted into the database.
RECORD_REFERENCE = dict(  # noqa: C408
    unspecified="FOO",
    boolean=True,
    short=42,
    int=42,
    long=42,
    float=42.42,
    double=42.42,
    naive_date=86400000,
    naive_datetime=86400000,
    utc_datetime=86400000,
    decimal=42.42,
    binary="\\0x00\\0x01",
    string="Hotzenplotz",
    json={"count": 42, "foo": "bar"},
    xml="XML",
    naive_time=45296000,
    __fivetran_synced=mock.ANY,
    __fivetran_id="zyx-987-abc",
    __fivetran_deleted=False,
)


@pytest.mark.parametrize("services", ["./tests/data/fivetran_canonical"], indirect=True)
def test_integration_fivetran(capfd, services):
    """
    Verify the Fivetran destination tester runs to completion with Fivetran test data.
    """

    # Read out stdout and stderr.
    _, err = capfd.readouterr()

    # "Truncate" is the last software test invoked by the Fivetran destination tester.
    # If the test case receives the corresponding log output, it is considered to be complete.
    assert "Create Table succeeded: transaction" in err
    assert "Updating definition for table: transaction" in err
    assert "Alter Table succeeded: transaction" in err
    assert "WriteBatch succeeded: transaction" in err

    assert "Create Table succeeded: campaign" in err
    assert "WriteBatch succeeded: campaign" in err
    assert "Truncate succeeded: campaign" in err
    assert "Hard Truncate succeeded: campaign" in err

    assert "Create Table succeeded: composite_table" in err
    assert "Updating definition for table: composite_table" in err
    assert "Alter Table succeeded: composite_table" in err
    assert "WriteBatch succeeded: composite_table" in err
    assert "Truncating: composite_table" in err
    assert "Truncate succeeded: composite_table" in err

    assert "Describe Table: transaction" in err
    assert "Describe Table: campaign" in err
    assert "Describe Table: composite_table" in err


@pytest.mark.parametrize("services", ["./tests/data/fivetran_migrations_ddl"], indirect=True)
def test_integration_fivetran_migrations_ddl(capfd, services):
    """
    Verify the Fivetran destination tester runs to completion with Fivetran test data.
    """

    # Read out stdout and stderr.
    _, err = capfd.readouterr()

    assert "Describe Table: transaction" in err


@pytest.mark.parametrize("services", ["./tests/data/fivetran_migrations_dml"], indirect=True)
def test_integration_fivetran_migrations_dml(capfd, services):
    """
    Verify the Fivetran destination tester runs to completion with Fivetran test data.
    """

    # Read out stdout and stderr.
    _, err = capfd.readouterr()

    assert "Describe Table: transaction" in err
    assert "Describe Table: transaction_renamed" in err


@pytest.mark.parametrize("services", ["./tests/data/fivetran_migrations_sync"], indirect=True)
def test_integration_fivetran_migrations_sync(capfd, services):
    """
    Verify the Fivetran destination tester runs to completion with Fivetran test data.
    """

    # Read out stdout and stderr.
    out, err = capfd.readouterr()

    assert "Describe Table: transaction" in err
    assert "Describe Table: transaction_history" in err
    assert "Describe Table: new_transaction_history" in err


@pytest.mark.parametrize("services", ["./tests/data/cratedb_canonical"], indirect=True)
def test_integration_cratedb(capfd, services, engine):
    """
    Verify the Fivetran destination tester runs to completion with CrateDB test data.
    """
    metadata = sa.MetaData()

    table_current = sa.Table(  # noqa: F841
        "all_types",
        metadata,
        schema="tester",
        quote_schema=True,
        autoload_with=engine,
    )

    table_reference = sa.Table(
        "all_types",
        metadata,
        sa.Column("unspecified", sa.String),
        sa.Column("bool", sa.Boolean),
        sa.Column("short", sa.SmallInteger),
        sa.Column("int", sa.Integer),
        sa.Column("long", sa.BigInteger),
        sa.Column("float", sa.Float),
        sa.Column("double", sa.Float),
        # FIXME: Investigate why `UserDefinedType` is used here.
        sa.Column("naive_date", UserDefinedType),
        sa.Column("naive_datetime", UserDefinedType),
        sa.Column("utc_datetime", UserDefinedType),
        sa.Column("decimal", sa.DECIMAL),
        sa.Column("binary", sa.Text),
        sa.Column("string", sa.String),
        sa.Column("json", ObjectType),
        sa.Column("xml", sa.String),
        sa.Column("naive_time", UserDefinedType),
        sa.Column("__fivetran_synced", UserDefinedType),
        sa.Column("__fivetran_id", sa.String),
        sa.Column("__fivetran_deleted", sa.Boolean),
        schema="tester_reference",
        quote_schema=True,
    )
    table_reference.schema = "tester"

    # Compare table schema.
    # FIXME: Comparison does not work like this, yet.
    #        Use Alembic's `compare()` primitive?
    # assert table_current == table_reference  # noqa: ERA001

    # Compare table content.
    with engine.connect() as connection:
        records = connection.execute(sa.text("SELECT * FROM tester.all_types")).mappings().one()
        assert records == RECORD_REFERENCE

    # Read out stdout and stderr.
    _, err = capfd.readouterr()

    # If the test case receives the corresponding log output, it is considered to be complete.
    assert "Create Table succeeded: all_types" in err
    assert "WriteBatch succeeded: all_types" in err
