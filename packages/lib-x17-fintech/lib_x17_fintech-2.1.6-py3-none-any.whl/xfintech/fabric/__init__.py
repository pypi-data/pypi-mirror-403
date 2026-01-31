"""
Fabric module for defining data structures with column and table information.

This module provides classes for describing data schemas:
- ColumnInfo: Metadata about individual columns (name, type, description)
- ColumnKind: Enum of supported column data types
- TableInfo: Metadata about tables and their column structure
"""

from .column.info import ColumnInfo
from .column.kind import ColumnKind
from .table.info import TableInfo

__all__ = [
    "ColumnInfo",
    "ColumnKind",
    "TableInfo",
]
