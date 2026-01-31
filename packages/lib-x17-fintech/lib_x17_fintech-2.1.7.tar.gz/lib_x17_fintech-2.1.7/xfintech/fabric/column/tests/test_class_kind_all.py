from __future__ import annotations

from xfintech.fabric.column.kind import ColumnKind


def test_datakind_members_exist():
    assert ColumnKind.INTEGER.value == "Integer"
    assert ColumnKind.FLOAT.value == "Float"
    assert ColumnKind.STRING.value == "String"
    assert ColumnKind.BOOLEAN.value == "Boolean"
    assert ColumnKind.DATETIME.value == "Datetime"
    assert ColumnKind.CATEGORICAL.value == "Categorical"
    assert ColumnKind.DATE.value == "Date"


def test_from_str_basic_cases():
    assert ColumnKind.from_str("Integer") == ColumnKind.INTEGER
    assert ColumnKind.from_str("Float") == ColumnKind.FLOAT
    assert ColumnKind.from_str("String") == ColumnKind.STRING
    assert ColumnKind.from_str("Boolean") == ColumnKind.BOOLEAN
    assert ColumnKind.from_str("Datetime") == ColumnKind.DATETIME
    assert ColumnKind.from_str("Categorical") == ColumnKind.CATEGORICAL


def test_from_str_case_insensitive():
    assert ColumnKind.from_str("integer") == ColumnKind.INTEGER
    assert ColumnKind.from_str("FLOAT") == ColumnKind.FLOAT
    assert ColumnKind.from_str("sTrInG") == ColumnKind.STRING
    assert ColumnKind.from_str("boolean") == ColumnKind.BOOLEAN
    assert ColumnKind.from_str("DATETIME") == ColumnKind.DATETIME
    assert ColumnKind.from_str("cAtEgOrIcAl") == ColumnKind.CATEGORICAL


def test_from_str_unknown_returns_unknown():
    assert ColumnKind.from_str("SomethingElse") == ColumnKind.STRING
    assert ColumnKind.from_str("") == ColumnKind.STRING
    assert ColumnKind.from_str("???") == ColumnKind.STRING


def test_str_representation():
    assert str(ColumnKind.INTEGER) == "Integer"
    assert str(ColumnKind.STRING) == "String"
    assert str(ColumnKind.DATE) == "Date"


def test_repr_representation():
    assert repr(ColumnKind.INTEGER) == "ColumnKind.INTEGER"
    assert repr(ColumnKind.CATEGORICAL) == "ColumnKind.CATEGORICAL"


def test_equality_with_string():
    assert ColumnKind.INTEGER == "Integer"
    assert ColumnKind.FLOAT == "float"
    assert ColumnKind.STRING != "Boolean"
    assert ColumnKind.DATETIME != "datetime2"
    assert ColumnKind.CATEGORICAL == "CATEGORICAL"


def test_inequality_with_string():
    assert ColumnKind.INTEGER != "Float"
    assert ColumnKind.BOOLEAN != "boolean2"
    assert ColumnKind.DATE != "DateTime"


def test_equality_with_enum():
    assert ColumnKind.INTEGER == ColumnKind.INTEGER
    assert ColumnKind.FLOAT != ColumnKind.STRING
    assert ColumnKind.DATE == ColumnKind.DATE


def test_inequality_with_enum():
    assert ColumnKind.INTEGER != ColumnKind.FLOAT
    assert ColumnKind.BOOLEAN != ColumnKind.DATETIME
    assert ColumnKind.CATEGORICAL != ColumnKind.DATE


def test_missing_method():
    assert ColumnKind("integer") == ColumnKind.INTEGER
    assert ColumnKind("FLOAT") == ColumnKind.FLOAT
    assert ColumnKind("unknown_value") == ColumnKind.STRING
