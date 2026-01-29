import dataclasses
import re
import typing as t

import pytest

from cratedb_fivetran_destination.model import CrateDBKnowledge, SqlBag
from fivetran_sdk import common_pb2


def test_sqlbag(engine):
    bag = SqlBag().add("SELECT 23").add("SELECT 42")
    with engine.connect() as connection:
        bag.execute(connection)


def test_sqlbag_add_wrong_none():
    bag = SqlBag().add(None)
    assert bool(bag) is False


def test_sqlbag_add_wrong_type():
    with pytest.raises(TypeError) as excinfo:
        SqlBag().add(42)
    excinfo.match(re.escape('Input SQL must be str, SqlBag, or SqlStatement, not "int"'))


def test_cratedb_knowledge_invalid_time():
    """
    Validate an error path of CrateDB-specific modifications around `NAIVE_TIME`.
    """

    @dataclasses.dataclass
    class PseudoRequest:
        table: t.Any

    table = common_pb2.Table()
    column = common_pb2.Column()
    column.name = "naive_time"
    column.type = common_pb2.DataType.NAIVE_TIME
    table.columns.append(column)

    request = PseudoRequest(table=table)
    record = {"naive_time": "INVALID"}

    with pytest.raises(ValueError) as excinfo:
        CrateDBKnowledge.replace_values(request, record)
    excinfo.match(
        "Invalid NAIVE_TIME value 'INVALID' for column 'naive_time': Unknown string format: INVALID"
    )
