import pytest

from xfintech.fabric.column.info import ColumnInfo, ColumnKind


def test_columninfo_basic_init():
    col = ColumnInfo(
        name="price",
        kind="Float",
        desc=" 股票价格 ",
        meta={"unit": "CNY"},
    )
    assert col.name == "price"
    assert col.kind == ColumnKind.FLOAT
    assert col.desc == "股票价格"
    assert col.meta == {"unit": "CNY"}


def test_columninfo_name_must_be_valid():
    with pytest.raises(ValueError):
        ColumnInfo(name="1invalid")


def test_columninfo_name_is_lowercase():
    col = ColumnInfo(name="PriceHigh")
    assert col.name == "pricehigh"


def test_columninfo_kind_from_datakind_instance():
    col = ColumnInfo(name="qty", kind=ColumnKind.INTEGER)
    assert col.kind == ColumnKind.INTEGER
    assert col.name == "qty"
    assert col.meta is None


def test_columninfo_kind_from_str_case_insensitive():
    col = ColumnInfo(name="qty", kind="integer")
    assert col.kind == ColumnKind.INTEGER
    assert col.name == "qty"

    col2 = ColumnInfo(name="qty", kind="InTeGeR")
    assert col2.kind == ColumnKind.INTEGER
    assert col2.name == "qty"


def test_columninfo_invalid_kind():
    col = ColumnInfo(name="x", kind="NOT_A_TYPE")
    assert col.kind == ColumnKind.STRING
    assert col.desc == ""
    assert col.meta is None


def test_columninfo_default_kind_string():
    col = ColumnInfo(name="remark")
    assert col.kind == ColumnKind.STRING
    assert col.meta is None


def test_columninfo_desc_strip():
    col = ColumnInfo(
        name="remark",
        desc="  Something Here   ",
    )
    assert col.desc == "Something Here"
    assert col.meta is None


def test_columninfo_desc_empty_when_none():
    col = ColumnInfo(name="remark", desc=None)
    assert col.desc == ""
    assert col.meta is None


def test_columninfo_meta_bytes_to_str():
    col = ColumnInfo(
        name="flag",
        meta={
            b"bin": b"yes",
            "code": b"ok",
        },
    )
    assert col.meta == {"bin": "yes", "code": "ok"}
    assert col.desc == ""


def test_columninfo_meta_str_normal():
    col = ColumnInfo(name="flag", meta={"x": 1})
    assert col.meta == {"x": 1}
    assert col.desc == ""


def test_columninfo_update_kind_desc_meta():
    col = ColumnInfo(
        name="price",
        kind="float",
        desc="old",
        meta={"unit": "CNY"},
    )
    col.update(
        kind="integer",
        desc="new-desc",
        meta={"precision": 2},
    )
    assert col.kind == ColumnKind.INTEGER
    assert col.desc == "new-desc"
    assert col.meta == {"unit": "CNY", "precision": 2}
    assert col.name == "price"


def test_columninfo_add_methods():
    col = ColumnInfo(name="level")
    col.add_desc("some desc")
    assert col.desc == "some desc"

    col.add_meta("k", "v")
    assert col.meta["k"] == "v"

    col.add_kind("Boolean")
    assert col.kind == ColumnKind.BOOLEAN


def test_full_columninfo_to_dict_and_describe():
    col = ColumnInfo(
        name="amount",
        kind="Float",
        desc="amt",
        meta={"unit": "usd"},
    )
    d1 = col.to_dict()
    assert d1["name"] == "amount"
    assert d1["kind"] == "Float"
    assert d1["desc"] == "amt"
    assert d1["meta"] == {"unit": "usd"}

    d2 = col.describe()
    assert d2["name"] == "amount"
    assert d2["kind"] == "Float"
    assert d2["desc"] == "amt"
    assert d2["meta"] == {"unit": "usd"}


def test_partial_columninfo_to_dict_and_describe():
    col2 = ColumnInfo(
        name="flag",
        kind="Boolean",
    )
    d3 = col2.to_dict()
    assert d3["name"] == "flag"
    assert d3["kind"] == "Boolean"
    assert d3["desc"] == ""
    assert d3["meta"] is None

    d4 = col2.describe()
    assert d4["name"] == "flag"
    assert d4["kind"] == "Boolean"
    assert "desc" not in d4
    assert "meta" not in d4


def test_columninfo_str_and_repr():
    col = ColumnInfo(name="price", kind="Float")
    s = str(col)
    assert "price: Float" in s

    r = repr(col)
    assert "name" in r
    assert "price" in r
    assert "Float" in r


def test_columninfo_identifier_is_deterministic():
    col1 = ColumnInfo(
        name="amount",
        kind="Float",
        desc="amt",
        meta={"unit": "usd"},
    )
    col2 = ColumnInfo(
        name="amount",
        kind="Float",
        desc="amt",
        meta={"unit": "usd"},
    )
    assert col1.identifier == col2.identifier


def test_columninfo_identifier_not_change_with_meta():
    col1 = ColumnInfo(
        name="amount",
        kind="Float",
        desc="amt",
        meta={"unit": "usd"},
    )
    col2 = ColumnInfo(
        name="amount",
        kind="Float",
        desc="amt",
        meta={"unit": "eur"},
    )
    col3 = ColumnInfo(
        name="volume",
        kind="Float",
        desc="amt",
        meta={"unit": "eur"},
    )
    assert col1.identifier == col2.identifier
    assert col1.identifier != col3.identifier
