import pytest

from xfintech.fabric.column.info import ColumnInfo
from xfintech.fabric.column.kind import ColumnKind
from xfintech.fabric.table.info import TableInfo


def test_tableinfo_basic_init():
    table = TableInfo(
        name="daily_market",
        desc=" 日线行情表 ",
        meta={"source": "tushare"},
        columns=[
            ColumnInfo(name="price", kind="Float", desc="收盘价"),
            ColumnInfo(name="volume", kind="Integer", desc="成交量"),
        ],
    )
    assert table.name == "daily_market"
    assert table.desc == "日线行情表"
    assert table.meta == {"source": "tushare"}
    assert len(table.columns) == 2
    assert "price" in table.columns
    assert "volume" in table.columns


def test_tableinfo_name_must_be_valid():
    with pytest.raises(ValueError):
        TableInfo(name="1invalid")


def test_tableinfo_name_is_lowercase():
    table = TableInfo(name="MyTable")
    assert table.name == "mytable"


def test_tableinfo_name_empty_when_none():
    table = TableInfo(name=None)
    assert table.name == ""


def test_tableinfo_name_accepts_underscore_hyphen():
    table1 = TableInfo(name="my_table")
    assert table1.name == "my_table"

    table2 = TableInfo(name="my-table")
    assert table2.name == "my-table"

    table3 = TableInfo(name="_private_table")
    assert table3.name == "_private_table"


def test_tableinfo_desc_strip():
    table = TableInfo(
        name="test",
        desc="  Something Here   ",
    )
    assert table.desc == "Something Here"


def test_tableinfo_desc_empty_when_none():
    table = TableInfo(name="test", desc=None)
    assert table.desc == ""


def test_tableinfo_meta_bytes_to_str():
    table = TableInfo(
        name="test",
        meta={
            b"bin": b"yes",
            "code": b"ok",
        },
    )
    assert table.meta == {"bin": "yes", "code": "ok"}


def test_tableinfo_meta_str_normal():
    table = TableInfo(name="test", meta={"x": 1, "y": "value"})
    assert table.meta == {"x": 1, "y": "value"}


def test_tableinfo_meta_none():
    table = TableInfo(name="test", meta=None)
    assert table.meta is None


def test_tableinfo_columns_from_columninfo_list():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
            ColumnInfo(name="volume", kind="Integer"),
        ],
    )
    assert len(table.columns) == 2
    assert table.columns["price"].kind == ColumnKind.FLOAT
    assert table.columns["volume"].kind == ColumnKind.INTEGER


def test_tableinfo_columns_from_dict_list():
    table = TableInfo(
        name="test",
        columns=[
            {"name": "price", "kind": "Float"},
            {"name": "volume", "kind": "Integer"},
        ],
    )
    assert len(table.columns) == 2
    assert table.columns["price"].kind == ColumnKind.FLOAT
    assert table.columns["volume"].kind == ColumnKind.INTEGER


def test_tableinfo_columns_mixed_types():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
            {"name": "volume", "kind": "Integer"},
        ],
    )
    assert len(table.columns) == 2
    assert isinstance(table.columns["price"], ColumnInfo)
    assert isinstance(table.columns["volume"], ColumnInfo)


def test_tableinfo_columns_invalid_type():
    with pytest.raises(TypeError):
        TableInfo(
            name="test",
            columns=["invalid"],
        )


def test_tableinfo_columns_none():
    table = TableInfo(name="test", columns=None)
    assert table.columns == {}


def test_tableinfo_get_column():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
            ColumnInfo(name="volume", kind="Integer"),
        ],
    )
    col = table.get_column("price")
    assert col is not None
    assert col.name == "price"
    assert col.kind == ColumnKind.FLOAT


def test_tableinfo_get_column_case_insensitive():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    col = table.get_column("PRICE")
    assert col is not None
    assert col.name == "price"


def test_tableinfo_get_column_not_exists():
    table = TableInfo(name="test", columns=[])
    col = table.get_column("nonexistent")
    assert col is None


def test_tableinfo_add_column():
    table = TableInfo(name="test")
    table.add_column(ColumnInfo(name="price", kind="Float"))

    assert len(table.columns) == 1
    assert "price" in table.columns
    assert table.columns["price"].kind == ColumnKind.FLOAT


def test_tableinfo_add_column_from_dict():
    table = TableInfo(name="test")
    table.add_column({"name": "price", "kind": "Float"})

    assert len(table.columns) == 1
    assert "price" in table.columns
    assert table.columns["price"].kind == ColumnKind.FLOAT


def test_tableinfo_remove_column():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
            ColumnInfo(name="volume", kind="Integer"),
        ],
    )
    table.remove_column("price")

    assert len(table.columns) == 1
    assert "price" not in table.columns
    assert "volume" in table.columns


def test_tableinfo_remove_column_case_insensitive():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    table.remove_column("PRICE")

    assert len(table.columns) == 0


def test_tableinfo_remove_column_not_exists():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    table.remove_column("nonexistent")

    assert len(table.columns) == 1


def test_tableinfo_update_column_kind_desc_meta():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(
                name="price",
                kind="Float",
                desc="old",
                meta={"unit": "CNY"},
            ),
        ],
    )
    table.update_column(
        "price",
        kind="Integer",
        desc="new-desc",
        meta={"precision": 2},
    )

    col = table.get_column("price")
    assert col.kind == ColumnKind.INTEGER
    assert col.desc == "new-desc"
    assert col.meta == {"unit": "CNY", "precision": 2}


def test_tableinfo_update_column_rename():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    table.update_column("price", new="new_price")

    assert "price" not in table.columns
    assert "new_price" in table.columns
    assert table.columns["new_price"].kind == ColumnKind.FLOAT


def test_tableinfo_update_column_not_exists():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    table.update_column("nonexistent", desc="new")

    assert len(table.columns) == 1
    assert table.columns["price"].desc == ""


def test_tableinfo_rename_column():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="old_name", kind="Float"),
        ],
    )
    table.rename_column("old_name", "new_name")

    assert "old_name" not in table.columns
    assert "new_name" in table.columns
    assert table.columns["new_name"].name == "new_name"


def test_tableinfo_rename_column_case_insensitive():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="old_name", kind="Float"),
        ],
    )
    table.rename_column("OLD_NAME", "new_name")

    assert "old_name" not in table.columns
    assert "new_name" in table.columns


def test_tableinfo_rename_column_not_exists():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    table.rename_column("nonexistent", "new_name")

    assert len(table.columns) == 1
    assert "new_name" not in table.columns


def test_tableinfo_list_columns():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
            ColumnInfo(name="volume", kind="Integer"),
        ],
    )
    cols = table.list_columns()

    assert len(cols) == 2
    assert all(isinstance(c, ColumnInfo) for c in cols)
    names = [c.name for c in cols]
    assert "price" in names
    assert "volume" in names


def test_tableinfo_list_columns_empty():
    table = TableInfo(name="test")
    cols = table.list_columns()

    assert cols == []


def test_tableinfo_full_describe():
    table = TableInfo(
        name="test",
        desc="Test table",
        meta={"source": "tushare"},
        columns=[
            ColumnInfo(name="price", kind="Float", desc="Price"),
        ],
    )
    d = table.describe()

    assert d["name"] == "test"
    assert d["desc"] == "Test table"
    assert d["meta"] == {"source": "tushare"}
    assert len(d["columns"]) == 1
    assert d["columns"][0]["name"] == "price"


def test_tableinfo_partial_describe():
    table = TableInfo(name="test")
    d = table.describe()
    assert "name" in d
    assert "desc" not in d
    assert "meta" not in d
    assert "columns" not in d


def test_tableinfo_full_to_dict():
    table = TableInfo(
        name="test",
        desc="Test table",
        meta={"source": "tushare"},
        columns=[
            ColumnInfo(name="price", kind="Float", desc="Price"),
        ],
    )
    d = table.to_dict()

    assert "identifier" in d
    assert d["name"] == "test"
    assert d["desc"] == "Test table"
    assert d["meta"] == {"source": "tushare"}
    assert len(d["columns"]) == 1


def test_tableinfo_from_dict():
    data = {
        "name": "test",
        "desc": "Test table",
        "meta": {"source": "tushare"},
        "columns": [
            {"name": "price", "kind": "Float"},
            {"name": "volume", "kind": "Integer"},
        ],
    }
    table = TableInfo.from_dict(data)

    assert table.name == "test"
    assert table.desc == "Test table"
    assert table.meta == {"source": "tushare"}
    assert len(table.columns) == 2


def test_tableinfo_from_dict_minimal():
    data = {}
    table = TableInfo.from_dict(data)

    assert table.name == ""
    assert table.desc == ""
    assert table.meta is None
    assert table.columns == {}


def test_tableinfo_str():
    table = TableInfo(
        name="test",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    s = str(table)
    assert "price" in s


def test_tableinfo_repr():
    table = TableInfo(name="test")
    r = repr(table)
    assert "TableInfo" in r
    assert "test" in r


def test_tableinfo_identifier_is_deterministic():
    table1 = TableInfo(
        name="test",
        desc="Test table",
        meta={"source": "tushare"},
        columns=[
            ColumnInfo(name="price", kind="Float"),
            ColumnInfo(name="volume", kind="Integer"),
        ],
    )
    table2 = TableInfo(
        name="test",
        desc="Test table",
        meta={"source": "tushare"},
        columns=[
            ColumnInfo(name="price", kind="Float"),
            ColumnInfo(name="volume", kind="Integer"),
        ],
    )
    assert table1.identifier == table2.identifier


def test_tableinfo_identifier_not_change_with_meta():
    table1 = TableInfo(
        name="test",
        desc="Test table",
        meta={"source": "tushare"},
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    table2 = TableInfo(
        name="test",
        desc="Test table",
        meta={"source": "yahoo"},
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    assert table1.identifier == table2.identifier


def test_tableinfo_identifier_changes_with_name():
    table1 = TableInfo(
        name="test1",
        desc="Test table",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    table2 = TableInfo(
        name="test2",
        desc="Test table",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    assert table1.identifier != table2.identifier


def test_tableinfo_identifier_changes_with_desc():
    table1 = TableInfo(
        name="test",
        desc="Desc1",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    table2 = TableInfo(
        name="test",
        desc="Desc2",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    assert table1.identifier != table2.identifier


def test_tableinfo_identifier_changes_with_columns():
    table1 = TableInfo(
        name="test",
        desc="Test table",
        columns=[
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    table2 = TableInfo(
        name="test",
        desc="Test table",
        columns=[
            ColumnInfo(name="volume", kind="Integer"),
        ],
    )
    assert table1.identifier != table2.identifier


def test_tableinfo_identifier_column_order_independent():
    table1 = TableInfo(
        name="test",
        desc="Test table",
        columns=[
            ColumnInfo(name="price", kind="Float"),
            ColumnInfo(name="volume", kind="Integer"),
        ],
    )
    table2 = TableInfo(
        name="test",
        desc="Test table",
        columns=[
            ColumnInfo(name="volume", kind="Integer"),
            ColumnInfo(name="price", kind="Float"),
        ],
    )
    assert table1.identifier == table2.identifier
