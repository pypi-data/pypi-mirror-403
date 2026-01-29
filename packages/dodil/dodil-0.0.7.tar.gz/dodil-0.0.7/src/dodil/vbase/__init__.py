"""Public surface for VBase.

Exports:
- VBaseClient / VBaseConfig / VBaseServiceHandle / VBaseError

Schema + advanced type re-exports (from PyMilvus):
- FieldSchema, CollectionSchema, DataType, IndexType
- IndexParams
- AnnSearchRequest, BaseRanker, Function

Note:
- PyMilvus is a required dependency for VBase runtime usage.
"""

from __future__ import annotations

from typing import Any

from .vbase_client import VBaseClient, VBaseServiceHandle, VBaseConfig, VBaseError


from pymilvus import CollectionSchema, DataType, FieldSchema, IndexType  # type: ignore
from pymilvus.client.abstract import AnnSearchRequest, BaseRanker, WeightedRanker  # type: ignore
from pymilvus.orm.collection import Function  # type: ignore
from pymilvus.milvus_client.index import IndexParams  # type: ignore


__all__ = [
    "VBaseClient",
    "VBaseConfig",
    "VBaseServiceHandle",
    "VBaseError",
    # PyMilvus schema helpers (lazy)
    "FieldSchema",
    "CollectionSchema",
    "DataType",
    "IndexType",
    "BaseRanker",
    "AnnSearchRequest",
    "WeightedRanker",
    "Function",
    "IndexParams",

]