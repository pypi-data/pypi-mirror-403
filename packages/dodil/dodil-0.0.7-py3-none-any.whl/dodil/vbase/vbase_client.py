"""VBase client backed by Milvus (PyMilvus).

This module provides a thin adapter that keeps your *DODIL* interface stable while
using `pymilvus` internally.

Auth note
---------
This client can run in two modes depending on what sits behind `uri`:
- Direct Milvus: PyMilvus typically expects Milvus credentials (often `username:password` token).
- VBase proxy: if your proxy expects an OIDC JWT, `_resolve_token()` will add the `Bearer ` prefix.

Make sure the token format you provide matches the backend you are connecting to.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Protocol, Union

from dodil.transport import TokenProvider

class VBaseError(RuntimeError):
    """High-level VBase client error."""

# PyMilvus is required at runtime for VBase.
# We import the types directly so engineers get strong typing + IDE autocomplete.
try:
    from pymilvus import CollectionSchema, DataType, FieldSchema  # type: ignore
    from pymilvus.client.abstract import AnnSearchRequest, BaseRanker, WeightedRanker  # type: ignore
    from pymilvus.orm.collection import Function  # type: ignore
    from pymilvus.milvus_client.index import IndexParams  # type: ignore
except Exception as e:  # pragma: no cover
    raise VBaseError(
        "PyMilvus is required for VBase. Install it with:\n"
        "  pip install pymilvus\n"
        "and ensure the version matches your Milvus server (Milvus 2.6.x -> PyMilvus 2.6.x)."
    ) from e


@dataclass(frozen=True)
class VBaseConfig:
    """Configuration for a VBase (Milvus) connection.

    You may specify either:
      - `uri` (recommended), e.g. "http://localhost:19530" or "https://milvus.example.com:443"
    OR
      - `host` + `port`, e.g. host="localhost", port=19530

    This is convenient when your platform displays address + port separately.
    """

    # Option A: full URI
    uri: Optional[str] = None

    # Option B: host + port
    host: Optional[str] = None
    port: Optional[int] = 443

    # If uri is not provided, scheme is used with host/port.
    scheme: str = "https"

    db_name: str = "default"

    # Pass-through kwargs for PyMilvus (e.g., secure=True, server_pem_path=..., etc.)
    # See PyMilvus connect() docs for supported fields.
    connect_kwargs: Optional[Dict[str, Any]] = None

    def resolved_uri(self) -> str:
        """Return a usable URI for PyMilvus."""
        if self.uri:
            return self.uri
        if self.host and self.port is not None:
            sch = (self.scheme or "http").rstrip(":")
            return f"{sch}://{self.host}:{int(self.port)}"
        raise VBaseError("VBaseConfig must provide either uri=... or host=... and port=...")


def _load_pymilvus():
    try:
        from pymilvus import MilvusClient  # type: ignore

        return MilvusClient
    except Exception as e:  # pragma: no cover
        raise VBaseError(
            "PyMilvus is not installed. Add `pymilvus` to your dependencies, e.g.\n"
            "  poetry add pymilvus\n"
            "and ensure the version matches your Milvus server (Milvus 2.6.x -> PyMilvus 2.6.x)."
        ) from e


class VBaseClient:
    """A thin, stable wrapper around `pymilvus.MilvusClient`.

    - Initialized with a `TokenProvider` (optional) and a VBaseConfig.
    - Lazily creates the underlying PyMilvus client.
    - If the token returned by TokenProvider changes, the underlying client is recreated.

    You can either use the wrapper methods or access the raw client via `.raw`.
    """

    def __init__(
        self,
        *,
        config: VBaseConfig,
        token_provider: Optional[TokenProvider] = None,
    ) -> None:
        self._cfg = config
        self._token_provider = token_provider

        self._MilvusClient = _load_pymilvus()
        self._client = None
        self._last_token: Optional[str] = None

    # -------------------------
    # Lifecycle
    # -------------------------

    def close(self) -> None:
        """Close the underlying client if it exposes a close method."""
        if self._client is None:
            return
        close_fn = getattr(self._client, "close", None)
        if callable(close_fn):
            try:
                close_fn()
            except Exception:
                # best-effort
                pass
        self._client = None
        self._last_token = None

    def __enter__(self) -> "VBaseClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # -------------------------
    # Raw access
    # -------------------------

    @property
    def raw(self):
        """Return the underlying `pymilvus.MilvusClient` (lazy-initialized)."""
        return self._ensure_client()

    # -------------------------
    # Internal helpers
    # -------------------------

    def _resolve_token(self) -> Optional[str]:
        if self._token_provider is None:
            return None
        tok = self._token_provider.get_access_token()
        if not tok:
            return None
        # Ensure Bearer prefix (avoid double-prefixing)
        if tok.lower().startswith("bearer "):
            return tok
        return f"Bearer {tok}"

    def _ensure_client(self):
        token = self._resolve_token()

        # Reuse existing client if token is unchanged.
        if self._client is not None and token == self._last_token:
            return self._client

        # Token changed or no client yet -> recreate.
        if self._client is not None:
            self.close()

        kwargs = dict(self._cfg.connect_kwargs or {})

        try:
            self._client = self._MilvusClient(
                uri=self._cfg.resolved_uri(),
                token=token,
                db_name=self._cfg.db_name,
                **kwargs,
            )
            self._last_token = token
            return self._client
        except Exception as e:
            raise VBaseError(f"Failed to connect to Milvus via PyMilvus: {e}") from e



    # -------------------------
    # Minimal wrapper API (PyMilvus MilvusClient signature)
    # -------------------------

    def list_collections(self, **kwargs: Any) -> List[str]:
        """List collections (mirrors `pymilvus.MilvusClient.list_collections`)."""
        return list(self._ensure_client().list_collections(**kwargs))

    def has_collection(self, collection_name: str, timeout: Optional[float] = None, **kwargs: Any) -> bool:
        """Check if a collection exists (mirrors `pymilvus.MilvusClient.has_collection`)."""
        return bool(self._ensure_client().has_collection(collection_name, timeout=timeout, **kwargs))

    def describe_collection(self, collection_name: str, timeout: Optional[float] = None, **kwargs: Any) -> Dict[str, Any]:
        """Describe a collection (mirrors `pymilvus.MilvusClient.describe_collection`)."""
        return dict(self._ensure_client().describe_collection(collection_name, timeout=timeout, **kwargs))

    def create_collection(
        self,
        collection_name: str,
        dimension: Optional[int] = None,
        primary_field_name: str = "id",
        id_type: str = "int",
        vector_field_name: str = "vector",
        metric_type: str = "COSINE",
        auto_id: bool = False,
        timeout: Optional[float] = None,
        schema: Optional[CollectionSchema] = None,
        index_params: Optional[IndexParams] = None,
        **kwargs: Any,
    ) -> Any:
        """Create a collection (mirrors `pymilvus.MilvusClient.create_collection`)."""
        return self._ensure_client().create_collection(
            collection_name=collection_name,
            dimension=dimension,
            primary_field_name=primary_field_name,
            id_type=id_type,
            vector_field_name=vector_field_name,
            metric_type=metric_type,
            auto_id=auto_id,
            timeout=timeout,
            schema=schema,
            index_params=index_params,
            **kwargs,
        )

    def drop_collection(self, collection_name: str, timeout: Optional[float] = None, **kwargs: Any) -> Any:
        """Drop a collection (mirrors `pymilvus.MilvusClient.drop_collection`)."""
        return self._ensure_client().drop_collection(collection_name, timeout=timeout, **kwargs)

    def insert(
        self,
        collection_name: str,
        data: Union[Dict, List[Dict]],
        timeout: Optional[float] = None,
        partition_name: Optional[str] = "",
        **kwargs: Any,
    ) -> Dict:
        """Insert rows (mirrors `pymilvus.MilvusClient.insert`)."""
        return self._ensure_client().insert(
            collection_name=collection_name,
            data=data,
            timeout=timeout,
            partition_name=partition_name,
            **kwargs,
        )

    def upsert(
        self,
        collection_name: str,
        data: Union[Dict, List[Dict]],
        timeout: Optional[float] = None,
        partition_name: Optional[str] = "",
        **kwargs: Any,
    ) -> Dict:
        """Upsert rows (mirrors `pymilvus.MilvusClient.upsert`)."""
        return self._ensure_client().upsert(
            collection_name=collection_name,
            data=data,
            timeout=timeout,
            partition_name=partition_name,
            **kwargs,
        )

    def search(
        self,
        collection_name: str,
        data: Optional[Union[List[list], list]] = None,
        filter: str = "",
        limit: int = 10,
        output_fields: Optional[List[str]] = None,
        search_params: Optional[dict] = None,
        timeout: Optional[float] = None,
        partition_names: Optional[List[str]] = None,
        anns_field: Optional[str] = None,
        ids: Optional[Union[List[int], List[str], str, int]] = None,
        **kwargs: Any,
    ) -> Any:
        """Vector search (mirrors `pymilvus.MilvusClient.search`)."""
        return self._ensure_client().search(
            collection_name=collection_name,
            data=data,
            filter=filter,
            limit=limit,
            output_fields=output_fields,
            search_params=search_params,
            timeout=timeout,
            partition_names=partition_names,
            anns_field=anns_field,
            ids=ids,
            **kwargs,
        )

    def query(
        self,
        collection_name: str,
        filter: str = "",
        output_fields: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        ids: Optional[Union[List, str, int]] = None,
        partition_names: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Any:
        """Query scalar fields (mirrors `pymilvus.MilvusClient.query`)."""
        return self._ensure_client().query(
            collection_name=collection_name,
            filter=filter,
            output_fields=output_fields,
            timeout=timeout,
            ids=ids,
            partition_names=partition_names,
            **kwargs,
        )


    def delete(
        self,
        collection_name: str,
        ids: Optional[Union[list, str, int]] = None,
        timeout: Optional[float] = None,
        filter: Optional[str] = None,
        partition_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Delete by ids or filter (mirrors `pymilvus.MilvusClient.delete`)."""
        return self._ensure_client().delete(
            collection_name=collection_name,
            ids=ids,
            timeout=timeout,
            filter=filter,
            partition_name=partition_name,
            **kwargs,
        )



    # -------------------------
    # Index management
    # -------------------------

    def create_index(
        self,
        collection_name: str,
        index_params: IndexParams,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """Create one or more indexes (mirrors `pymilvus.MilvusClient.create_index`).

        Note: `index_params` is typically an `IndexParams` instance from PyMilvus.
        """
        return self._ensure_client().create_index(
            collection_name=collection_name,
            index_params=index_params,
            timeout=timeout,
            **kwargs,
        )

    def list_indexes(
        self,
        collection_name: str,
        field_name: Optional[str] = "",
        **kwargs: Any,
    ) -> Any:
        """List index names (mirrors `pymilvus.MilvusClient.list_indexes`)."""
        return self._ensure_client().list_indexes(
            collection_name=collection_name,
            field_name=field_name or "",
            **kwargs,
        )

    def describe_index(
        self,
        collection_name: str,
        index_name: str,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """Describe an index (mirrors `pymilvus.MilvusClient.describe_index`)."""
        return self._ensure_client().describe_index(
            collection_name=collection_name,
            index_name=index_name,
            timeout=timeout,
            **kwargs,
        )

    def drop_index(
        self,
        collection_name: str,
        index_name: str,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """Drop an index (mirrors `pymilvus.MilvusClient.drop_index`)."""
        return self._ensure_client().drop_index(
            collection_name=collection_name,
            index_name=index_name,
            timeout=timeout,
            **kwargs,
        )

    # -------------------------
    # Load / unload
    # -------------------------

    def load_collection(
        self,
        collection_name: str,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """Load a collection into memory (mirrors `pymilvus.MilvusClient.load_collection`)."""
        return self._ensure_client().load_collection(
            collection_name=collection_name,
            timeout=timeout,
            **kwargs,
        )

    def release_collection(
        self,
        collection_name: str,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """Unload a collection from memory (mirrors `pymilvus.MilvusClient.release_collection`)."""
        return self._ensure_client().release_collection(
            collection_name=collection_name,
            timeout=timeout,
            **kwargs,
        )

    def get_load_state(
        self,
        collection_name: str,
        partition_name: Optional[str] = "",
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """Get load state (mirrors `pymilvus.MilvusClient.get_load_state`).

        Returns a dict-like payload (e.g. state + progress when loading).
        """
        return self._ensure_client().get_load_state(
            collection_name=collection_name,
            partition_name=partition_name or "",
            timeout=timeout,
            **kwargs,
        )

    def refresh_load(
        self,
        collection_name: str,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """Refresh a loaded collection (mirrors `pymilvus.MilvusClient.refresh_load`)."""
        return self._ensure_client().refresh_load(
            collection_name=collection_name,
            timeout=timeout,
            **kwargs,
        )

    # -------------------------
    # Hybrid search
    # -------------------------

    def hybrid_search(
        self,
        collection_name: str,
        reqs: List[AnnSearchRequest],
        ranker: Union[BaseRanker, Function],
        limit: int = 10,
        output_fields: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        partition_names: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Any:
        """Hybrid (multi-vector) search with reranking (mirrors `pymilvus.MilvusClient.hybrid_search`).

        Note: `reqs` is typically a list of `AnnSearchRequest` and `ranker` is a `BaseRanker` or
        `Function` depending on your PyMilvus usage.
        """
        return self._ensure_client().hybrid_search(
            collection_name=collection_name,
            reqs=reqs,
            ranker=ranker,
            limit=limit,
            output_fields=output_fields,
            timeout=timeout,
            partition_names=partition_names,
            **kwargs,
        )



class _ClientLike(Protocol):
    token_provider: Optional[TokenProvider]


class VBaseServiceHandle:
    """Lazy service handle for VBase.

    Usage:
      vbase = client.vbase.connect(VBaseConfig(...))
      vbase.list_collections()
    """

    def __init__(
        self,
        owner: Optional[_ClientLike] = None,
        *,
        default_config: Optional[VBaseConfig] = None,
        token_provider: Optional[TokenProvider] = None,
    ) -> None:
        self._owner = owner
        self._default_config = default_config
        self._token_provider_override = token_provider

    def connect(
        self,
        config: Optional[VBaseConfig] = None,
        *,
        token_provider: Optional[TokenProvider] = None,
    ) -> VBaseClient:
        """Create a bound VBaseClient.

        Token provider resolution priority:
          explicit arg > handle override > owner.token_provider
        """
        cfg = config or self._default_config
        if cfg is None:
            raise VBaseError("VBaseServiceHandle.connect() requires a VBaseConfig")

        provider = token_provider or self._token_provider_override or getattr(self._owner, "token_provider", None)

        return VBaseClient(config=cfg, token_provider=provider)
