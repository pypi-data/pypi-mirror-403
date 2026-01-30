from __future__ import annotations
import asyncio
import time
import os
import httpx
import mimetypes
from enum import IntEnum
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, List, TYPE_CHECKING, Union

from dodil.common import Profile, _api_grpc_target
from dodil.transport import TokenProvider, AsyncGrpcTransport

if TYPE_CHECKING:
    from dodil.vng.v1.vng_pb2_grpc import VngServiceStub
    from dodil.vng.v1.vng_pb2 import (
        IngestRequest, 
        InputSpec, 
        EmbedSpec, 
        GetJobRequest, 
        Input, 
        Locator, 
        TextLocator,
    )

class EmbeddingTask(IntEnum):
    INDEX = 0
    QUERY = 1
    CODE_INDEX = 2
    CODE_QUERY = 3
    TEXT_SIMILARITY = 4

def _get_vng_pb2():
    try:
        from dodil.vng.v1 import vng_pb2
        return vng_pb2
    except ImportError as e:
        raise ImportError(
            "Helper 'vng.embed()' requires generated protos. "
        ) from e

def _get_vng_grpc():
    try:
        from dodil.vng.v1 import vng_pb2_grpc
        return vng_pb2_grpc
    except ImportError as e:
        raise ImportError(
            "Helper 'vng.embed()' requires generated protos. "
        ) from e


@dataclass
class VngInput:
    """Helper to specify non-text inputs (images, files, URLs) for VNG embedding."""
    locator_type: str  # "text", "file", "url", "s3", "bytes"
    value: Any
    name_hint: Optional[str] = None
    kind_hint: Optional[str] = None  # e.g. "IMAGE", "VIDEO"

    @property
    def source(self) -> str:
        """Returns a string representation (e.g. the text, URL, path)."""
        if self.locator_type == "text": return str(self.value)
        if self.locator_type in ("url", "file", "s3"): return str(self.value)
        return "<bytes>"
    
    @classmethod
    def as_text(cls, text: str) -> "VngInput":
        return cls("text", text, kind_hint="TEXT")

    @classmethod
    def as_url(cls, url: str, kind: Optional[str] = None) -> "VngInput":
        return cls("url", url, kind_hint=kind)
        
    @classmethod
    def as_file(cls, path: str, kind: Optional[str] = None) -> "VngInput":
        """For local file paths that the server can access (e.g. shared volume) or just holding the path."""
        # Note: 'FileLocator' in proto usually means a path capable of being read by the service.
        return cls("file", path, kind_hint=kind)

    @classmethod
    def as_s3(cls, key: str, kind: Optional[str] = None) -> "VngInput":
        return cls("s3", key, kind_hint=kind)

    @classmethod
    def as_bytes(cls, data: bytes, name_hint: Optional[str] = None, kind: Optional[str] = None) -> "VngInput":
        return cls("bytes", data, name_hint=name_hint, kind_hint=kind)

    @classmethod
    def from_any(cls, item: Union[str, "VngInput"]) -> "VngInput":
        """
        Smartly create a VngInput from a string or return as-is.
        
        For strings, it infers the kind (IMAGE, VIDEO, DOCUMENT) based on file extension
        or known URL patterns. For ambiguous URLs (like Google Drive or S3 presigned URLs 
        without extension), it attempts a lightweight network check (HEAD request) to 
        determine the Content-Type.
        """
        if isinstance(item, VngInput):
            return item
            
        if isinstance(item, str):
            kind = None
            
            # 1. Try mimetypes detection on path (ignoring query/fragment)
            clean_path = item.split('?')[0].split('#')[0]
            # Only use mimetypes if there is an extension-like structure
            if "." in os.path.basename(clean_path):
                mime_type, _ = mimetypes.guess_type(clean_path)
                
                if mime_type:
                    if mime_type.startswith("image/"):
                        kind = "IMAGE"
                    elif mime_type.startswith("video/"):
                        kind = "VIDEO"
                    elif mime_type.startswith("audio/"):
                        kind = "AUDIO"
                    elif mime_type.startswith("application/pdf"):
                        kind = "DOCUMENT"
                    elif mime_type.startswith("text/plain") or mime_type.startswith("text/markdown"):
                        kind = "DOCUMENT"

            # 2. Fallback manual extension checks
            if not kind:
                lower = clean_path.lower()
                if lower.endswith(('.docx', '.doc', '.md', '.markdown')):
                    kind = "DOCUMENT"
            
            # 3. Domain heuristics (Basic)
            if not kind:
                if "youtube.com" in item or "youtu.be" in item:
                    kind = "VIDEO"

            # 4. Network Check for http(s) URLs if kind is still unknown
            # This handles Google Drive links or signed URLs without extensions.
            if not kind and (item.startswith("http://") or item.startswith("https://")):
                ctype = cls._resolve_content_type_network(item)
                if ctype:
                    if ctype.startswith("image/"): kind = "IMAGE"
                    elif ctype.startswith("video/"): kind = "VIDEO"
                    elif ctype.startswith("audio/"): kind = "AUDIO"
                    elif ctype == "application/pdf": kind = "DOCUMENT"
                    elif "wordprocessingml" in ctype or "msword" in ctype: kind = "DOCUMENT"
                    elif ctype.startswith("text/"): kind = "DOCUMENT"

            # Create the input
            if item.startswith("http://") or item.startswith("https://"):
                return cls.as_url(item, kind=kind)
            elif item.startswith("s3://"):
                return cls.as_s3(item, kind=kind)
            elif os.path.exists(item):
                return cls.as_file(item, kind=kind)
            else:
                return cls("text", str(item), kind_hint=kind or "TEXT")
        
        # Fallback for unknown types
        return cls("text", str(item), kind_hint="TEXT")

    @staticmethod
    def _resolve_content_type_network(url: str) -> Optional[str]:
        """Helper to resolve content-type via HEAD/GET request with timeout."""
        try:
            target_url = url
            # Special handling for Google Drive view links -> convert to download link
            if "drive.google.com" in url and "/file/d/" in url:
                parts = url.split("/file/d/")
                if len(parts) > 1:
                    file_id = parts[1].split("/")[0]
                    # Use export=download to get the actual file content type
                    target_url = f"https://drive.google.com/uc?id={file_id}&export=download"

            # Use verify=False to be robust against cert issues in some envs, 
            # and short timeout to avoid blocking.
            with httpx.Client(timeout=3.0, verify=False, follow_redirects=True) as client:
                try:
                    # 1. Try HEAD first
                    resp = client.head(target_url)
                    if resp.status_code == 405: # Method Not Allowed
                         raise httpx.RequestError("Method not allowed")
                except (httpx.RequestError, httpx.HTTPStatusError):
                    # 2. Fallback to GET with Range header (fetch only first byte)
                    # This works for many servers including S3/Google Drive to get headers
                    resp = client.get(target_url, headers={"Range": "bytes=0-0"})
                
                if resp.status_code < 400:
                    return resp.headers.get("content-type")
                
                return None
        except Exception:
            # Swallow errors to prevent crashing the ingest loop
            return None



@dataclass(frozen=True)
class VngConfig:
    """Configuration for the VNG service client.

    VNG primarily uses gRPC. We model `base_url` as either:
      - a full URL (e.g. https://vng.dev.dodil.io) OR
      - a gRPC target (e.g. vng.dev.dodil.io:443)
    """
    profile: Profile = "staging"

    timeout_s: float = 120.0
    verify_ssl: bool = True

    # Optional: include headers that should always be sent to VNG
    default_headers: Optional[Dict[str, str]] = None

    @property
    def resolved_target(self) -> str:
        return _api_grpc_target(self.profile)




class _ClientLike(Protocol):
    """
    Minimal protocol for the root Client object (if you have one).
    This lets VngServiceHandle depend on a narrow interface.
    """
    profile: Profile
    token_provider: Optional[TokenProvider]
    timeout_s: float
    verify_ssl: bool


class VngClient:
    """
    Concrete VNG client bound to a specific base_url + token provider + HTTP settings.
    """

    def __init__(
            self,
            *,
            target: str,
            token_provider: Optional[TokenProvider] = None,
            timeout_s: float = 120.0,
            verify_ssl: bool = True,
            default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        # NOTE: gRPC uses `target` (host:port). For TLS, pass secure=True.
        # `verify_ssl` is kept for parity with HTTP config; TLS verification is handled
        # by the underlying grpc channel credentials.
        
        # Heuristic for local dev: if target is localhost, default to insecure
        # unless port 443 is used or verify_ssl is explicitly True.
        # For remote targets, always default to secure (TLS).
        is_local = "localhost" in target or "127.0.0.1" in target
        # Default to secure
        use_secure = True
        if is_local and ":443" not in target and not verify_ssl:
            use_secure = False

        self.target = target
        self.token_provider = token_provider
        self.verify_ssl = verify_ssl

        print(f"[VngClient] Initializing client for target='{target}' secure={use_secure} (verify_ssl={verify_ssl})")

        self._grpc = AsyncGrpcTransport(
            target=target,
            token_provider=token_provider,
            secure=use_secure,
            default_metadata=default_headers,
            default_timeout_s=timeout_s,
        )

    @property
    def channel(self):
        """Expose the underlying grpc.aio.Channel for advanced usage."""
        return self._grpc.channel

    def stub(self, stub_cls, *args: Any, **kwargs: Any):
        """Construct a generated async stub bound to this client's channel."""
        return self._grpc.stub(stub_cls, *args, **kwargs)

    def embed(
        self,
        inputs: List[Union[str, VngInput]] = None,
        dim: Optional[int] = None,
        task: Optional[Union[EmbeddingTask, int, str]] = None,
        poll_interval: float = 0.5,
        timeout: float = 120.0,
        **kwargs,
    ) -> List[List[Dict[str, Any]]]:
        """
        High-level helper to embed a batch of inputs (text or VngInput objects).
        
        Submits an Ingest job and polls until completion.
        Returns a list of list of chunks (one list of chunks per input).
        Each chunk dict contains "vector", "text" (optional), "index".
        """
        # Backwards compatibility for 'texts' arg
        if inputs is None:
            inputs = kwargs.get("texts", [])

        # Smart input processing
        processed_inputs = [VngInput.from_any(item) for item in inputs]

        # Construct JSON payload for REST API
        inputs_json = []
        for idx, item in enumerate(processed_inputs):
            loc = {}
            kind_hint = "DATA_KIND_UNSPECIFIED"
            
            if isinstance(item, str):
                loc = {"text": {"text": item}}
                kind_hint = "DATA_KIND_TEXT"
            elif isinstance(item, VngInput):
                if item.kind_hint:
                    upper_kind = item.kind_hint.upper()
                    if upper_kind == "DOCUMENT":
                        # Server does not support DATA_KIND_DOCUMENT, map to FILE
                        kind_hint = "DATA_KIND_FILE"
                    else:
                        kind_hint = f"DATA_KIND_{upper_kind}"
                
                if item.locator_type == "text":
                    loc = {"text": {"text": item.value}}
                elif item.locator_type == "file":
                    loc = {"file": {"path": item.value}}
                elif item.locator_type == "url":
                    loc = {"url": {"url": item.value}}
                elif item.locator_type == "s3":
                    loc = {"s3": {"key": item.value}}
                elif item.locator_type == "bytes":
                    raise NotImplementedError("Bytes input not supported in REST mode yet")
            
            if loc:
                inp = {
                    "input_id": str(idx),
                    "locator": loc,
                    "kind_hint": kind_hint,
                    "meta": {}
                }
                inputs_json.append(inp)

        # Handle task enum -> string mapping if needed
        task_val = "EMBED_TASK_INDEX"
        if task is not None:
             if isinstance(task, EmbeddingTask):
                 # Map our enum names to proto names basic logic
                 # Our enum: INDEX, QUERY... Proto: EMBED_TASK_INDEX, EMBED_TASK_QUERY
                 task_val = f"EMBED_TASK_{task.name}"
             elif isinstance(task, int):
                 # Try to use generated proto if available, else best effort
                try:
                    pb2 = _get_vng_pb2()
                    task_val = pb2.EmbedTask.Name(task)
                except Exception:
                    # Fallback mapping if proto lib not present
                    # This assumes standard mapping 0->INDEX etc.
                    mapping = {
                        0: "EMBED_TASK_INDEX",
                        1: "EMBED_TASK_QUERY", 
                        2: "EMBED_TASK_CODE_INDEX",
                        3: "EMBED_TASK_CODE_QUERY",
                        4: "EMBED_TASK_TEXT_SIMILARITY"
                    }
                    task_val = mapping.get(task, str(task))
             else:
                task_val = str(task)

        req_json = {
            "input_spec": {
                "inputs": inputs_json,
                "meta": {}
            },
            "embed_spec": {
                "task": task_val,
                "grouped_inputs": False,
                "limit_to_context": False
            }
        }
        
        if dim is not None:
             req_json["embed_spec"]["dimension"] = dim

        # Determine HTTP URL from target
        host_port = self.target
        scheme = "https"
        if ":443" in host_port:
            host_only = host_port.replace(":443", "")
        elif ":80" in host_port:
            scheme = "http"
            host_only = host_port.replace(":80", "")
        else:
            host_only = host_port.split(":")[0]
            if not self.verify_ssl and "localhost" in host_only:
                 scheme = "http"

        base_url = f"{scheme}://{host_only}"
        if ":" in host_port and ":443" not in host_port and ":80" not in host_port:
             base_url = f"{scheme}://{host_port}"

        url = f"{base_url}/v1/vng/ingest"

        # print(f"[VngClient] Sending REST request to {url}")
        
        headers = {"Content-Type": "application/json"}
        if self.token_provider:
            token = self.token_provider.get_access_token()
            headers["Authorization"] = f"Bearer {token}"

        with httpx.Client(verify=self.verify_ssl, timeout=timeout) as client:
            # 1. Submit Ingest
            try:
                post_resp = client.post(url, json=req_json, headers=headers)
                post_resp.raise_for_status()
                resp_data = post_resp.json()
            except httpx.HTTPError as e:
                if hasattr(e, 'response'):
                    print(f"Error response: {e.response.text}")
                raise

            job_id = resp_data.get("job_id")
            if not job_id and "data" in resp_data and isinstance(resp_data["data"], dict):
                job_id = resp_data["data"].get("jobId") or resp_data["data"].get("job_id")

            if not job_id:
                 if resp_data.get("status") in ("done", "succeeded"):
                     return self._parse_rest_results(resp_data, len(inputs))
                 if "data" in resp_data and isinstance(resp_data["data"], dict):
                      inner_status = resp_data["data"].get("status")
                      if inner_status in ("done", "succeeded"):
                           return self._parse_rest_results(resp_data["data"], len(inputs))
                 raise RuntimeError(f"No job_id returned: {resp_data}")

            # 2. Poll for results
            start_time = time.time()
            job_url = f"{url}/{job_id}"
            
            while True:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Embedding job {job_id} timed out after {timeout}s")

                get_resp = client.get(job_url, headers=headers)
                get_resp.raise_for_status()
                job_data = get_resp.json()
                
                # Unwrap if necessary
                actual_data = job_data
                if "data" in job_data and isinstance(job_data["data"], dict):
                    if "status" in job_data["data"]:
                        actual_data = job_data["data"]

                status = actual_data.get("status", "").lower()
                
                if status in ("succeeded", "done"):
                    return self._parse_rest_results(actual_data, len(inputs))
                
                elif status == "failed":
                     err = actual_data.get("error", "Unknown error")
                     raise RuntimeError(f"Embedding job {job_id} failed: {err}")
                
                time.sleep(poll_interval)


    def _parse_rest_results(self, job_data, num_inputs) -> List[List[Dict[str, Any]]]:
        outputs = job_data.get("output", [])
        results_map = {}
        for out in outputs:
            inp_id = out.get("input_id") or out.get("inputId")
            chunks = out.get("chunks", [])
            
            chunk_list = []
            if chunks:
                for i, ch in enumerate(chunks):
                    emb = ch.get("embedding", [])
                    txt = ch.get("text")
                    if emb:
                        chunk_list.append({
                            "vector": emb,
                            "text": txt,
                            "index": i
                        })
            else:
                 print(f"[VngClient] Warning: No chunks/embedding for input {inp_id}")
            
            results_map[inp_id] = chunk_list
        
        ordered_results = []
        for i in range(num_inputs):
            ordered_results.append(results_map.get(str(i), []))
        return ordered_results
    
    def _grpc_embed_unused(self):
        pass

    def close(self) -> None:
        """Close the underlying resources (if any)."""
        # If transport is async, we can't await it here in sync mode easily.
        # But we primarily use REST/httpx.Client (context manager) in embed(),
        # so this is less critical unless we used the grpc channel elsewhere.
        pass


class VngServiceHandle:
    """
    Lazy service handle.

    - Safe to access as `c.vng` always.
    - Can be used directly: `c.vng.list_jobs()`, `c.vng.health()`
      (proxies to a lazily-created default client).
    - Can create a custom/bound client: `c.vng.connect(config=...)`.
    """

    def __init__(
            self,
            owner: Optional[_ClientLike] = None,
            *,
            config: Optional[VngConfig] = None,
            token_provider: Optional[TokenProvider] = None,
    ) -> None:
        self._owner = owner
        self._config = config or VngConfig(profile=getattr(owner, "profile", "staging"))
        self._token_provider_override = token_provider
        self._default_client: Optional[VngClient] = None


    def connect(
            self,
            *,
            config: Optional[VngConfig] = None,
            token_provider: Optional[TokenProvider] = None,
    ) -> VngClient:
        """
        Create a new VngClient instance.

        - If `config` is provided, it overrides handle config.
        - If `token_provider` is provided, it overrides both handle + owner provider.
        """
        cfg = config or self._config
        target = cfg.resolved_target

        # Resolve token provider priority:
        # explicit arg > handle override > owner provider (if any)
        provider = token_provider or self._token_provider_override or getattr(self._owner, "token_provider", None)

        # Resolve timeout/verify priority:
        # cfg values by default, but you can choose to inherit from owner if desired.
        timeout_s = cfg.timeout_s
        verify_ssl = cfg.verify_ssl
        headers = cfg.default_headers

        return VngClient(
            target=target,
            token_provider=provider,
            timeout_s=timeout_s,
            verify_ssl=verify_ssl,
            default_headers=headers,
        )
