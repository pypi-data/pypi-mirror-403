from __future__ import annotations
import uuid
from typing import List, Optional, Dict, Any, Union

from dodil.client import Client
from dodil.vng.vng_client import VngInput, EmbeddingTask
from dodil.vbase.vbase_client import VBaseConfig


class Space:
    """
    High-level structure combining VNG embedding and VBase storage/search.
    """
    def __init__(self, client: Client):
        self._client = client
        self.dim = 2048


    def setup(
        self,
        dim: int,
        index_type: str = "AUTOINDEX",
        metric_type: str = "COSINE"
    ) -> str:
        """
        Helper to set up a unique collection compatible with this space.
        Returns the name of the newly created collection.
        """
        # Import here to avoid hard dependency if not used
        try:
            from pymilvus import FieldSchema, CollectionSchema, DataType
        except ImportError:
            raise ImportError("pymilvus is required for setup")

        self.dim = dim
        vbase = self._client.vbase.connect()
        try:
            # Generate a unique name that doesn't exist
            while True:
                collection_name = f"col_{uuid.uuid4().hex}"
                if not vbase.raw.has_collection(collection_name):
                    break

            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
                # 65535 is max for Milvus VARCHAR
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="meta", dtype=DataType.JSON, nullable=True),
            ]
            
            schema = CollectionSchema(fields, description=f"Collection created by Dodil SDK for {collection_name}")
            vbase.raw.create_collection(collection_name, schema=schema)
            
            index_params = vbase.raw.prepare_index_params()
            index_params.add_index(field_name="vector", index_type=index_type, metric_type=metric_type)
            vbase.raw.create_index(collection_name, index_params)
            vbase.raw.load_collection(collection_name)
            
            return collection_name
        finally:
            vbase.close()


    def add(
        self,
        inputs: List[Union[str, VngInput]],
        collection_name: str,
        ids: Optional[List[Union[int, str]]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        vng_task: Union[EmbeddingTask, int, str] = EmbeddingTask.INDEX, # Typed as Any/str to allow EmbedTask enum or string
        vector_field: str = "vector",
        text_field: str = "text",
        vbase_config: Optional[VBaseConfig] = None,
        primary_field_name: str = "id",
        batch_size: int = 2,
        max_workers: int = 4,
    ) -> Dict[str, Any]:
        """
        Embeds inputs using VNG and inserts them into VBase (Milvus).
        Supports concurrent batch processing.
        
        Args:
            inputs: List of inputs (strings or VngInput mappings) to ingest.
            collection_name: Target VBase collection.
            ids: Optional list of IDs. If None, Milvus auto-id should be enabled in the collection.
            metadatas: Optional list of dicts with extra fields to insert.
            vng_task: VNG task type (e.g. EMBED_TASK_INDEX).
            vector_field: Name of the vector field in Milvus (default: "vector").
            text_field: Name of the text/source field in Milvus (default: "text").
            vbase_config: Optional config override for VBase connection.
            primary_field_name: Name of the primary key field if providing IDs (default: "id").
            batch_size: Number of items to process in one batch (default: 32).
            max_workers: Number of concurrent workers (default: 4).
        """
        if not inputs:
            return {"insert_count": 0}
            
        import concurrent.futures
        
        # Try to import tqdm
        tqdm_bar = None
        try:
            from tqdm import tqdm
            tqdm_bar = tqdm
        except ImportError:
            pass

        total = len(inputs)
        
        # If total is small enough, just run directly
        if total <= batch_size:
            return self._process_batch(
                inputs, collection_name, ids, metadatas, 
                vng_task, vector_field, text_field, vbase_config, primary_field_name
            )

        batches = []
        for i in range(0, total, batch_size):
            end = i + batch_size
            b_inputs = inputs[i:end]
            b_ids = ids[i:end] if ids else None
            b_metas = metadatas[i:end] if metadatas else None
            batches.append((b_inputs, b_ids, b_metas))

        total_inserted = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    self._process_batch, 
                    b_in, collection_name, b_id, b_meta, 
                    vng_task, vector_field, text_field, vbase_config, primary_field_name
                ) 
                for b_in, b_id, b_meta in batches
            ]
            
            iterator = concurrent.futures.as_completed(futures)
            if tqdm_bar:
                iterator = tqdm_bar(iterator, total=len(batches), desc="Creating Embeddings")
            else:
                print(f"Creating embeddings... ({len(batches)} batches)")
            
            for future in iterator:
                try:
                    res = future.result()
                    total_inserted += res.get("insert_count", 0)
                except Exception as e:
                    print(f"Batch embedding failed: {e}")
                    raise e
                    
        return {"insert_count": total_inserted}

    def _process_batch(
        self,
        inputs: List[Union[str, VngInput]],
        collection_name: str,
        ids: Optional[List[Union[int, str]]],
        metadatas: Optional[List[Dict[str, Any]]],
        vng_task: Union[EmbeddingTask, int, str],
        vector_field: str,
        text_field: str,
        vbase_config: Optional[VBaseConfig],
        primary_field_name: str,
    ) -> Dict[str, Any]:
        
        # Ensure thread has an event loop for grpc.aio
        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Normalize inputs to VngInput to access smart detection logic
        normalized_inputs = [VngInput.from_any(inp) for inp in inputs]

        # 1. Embed using VNG (Sync)
        vng = self._client.vng.connect()
        try:
            embeddings = vng.embed(
                inputs=normalized_inputs,
                task=vng_task,
                dim=self.dim
            )
        finally:
            vng.close()

        # 2. Prepare data for Milvus
        rows = []
        for i, (inp, vec) in enumerate(zip(normalized_inputs, embeddings)):
            # Determine what to store in the text/source field
            # VngInput.source returns the string val or <bytes>
            val_str = inp.source

            row = {
                text_field: val_str,
                vector_field: vec,
            }
            if ids is not None and i < len(ids):
                row[primary_field_name] = ids[i]
            
            # Handle metadata
            meta_dict = {}
            if metadatas and i < len(metadatas):
                meta_dict.update(metadatas[i])
            
            # Auto-populate 'type'/'kind' if not present
            # Checks if user schema has 'meta' field usually, but here we just preparing a dict to insert.
            # Milvus dynamic fields or JSON 'meta' field can take this.
            if inp.kind_hint:
                # We put it into 'meta' key if the schema expects a JSON field named 'meta',
                # OR we can put it as a direct field if using dynamic schema.
                # Based on test_integration, there is a "meta" JSON field.
                
                # If valid metadata dict passed, check if it has "meta" key
                user_meta = metadatas[i] if (metadatas and i < len(metadatas)) else {}
                
                # Strategy:
                # 1. If we have a dedicated JSON field 'meta' (usually), we merge into it.
                # 2. If 'meta' key exists in user input, we use it.
                # 3. If not, we create it.
                
                # Check if "meta" key is already in the row (from metadatas update)
                # or if we should add it.
                
                # To be safe and compatible with the specific test case:
                # The test expects `meta={"type": "text"}` structure.
                # So row["meta"] = {"type": ...}
                
                if "meta" in row:
                    # User provided specific meta
                    pass 
                else:
                    # Auto-fill
                    row["meta"] = {"type": inp.kind_hint.lower()}
            
            if metadatas and i < len(metadatas):
                # Apply user overrides again to ensure they take precedence if they conflict with auto-fill logic above
                # But wait, earlier simple `row.update` mixed top-level fields. 
                # If user passed {"meta": {...}}, it is in row["meta"].
                # If user passed {"some_col": 1}, it is in row["some_col"].
                row.update(metadatas[i])
            
            rows.append(row)

        # 3. Insert into VBase (Sync)
        vbase = self._client.vbase.connect(config=vbase_config)
        try:
            res = vbase.insert(collection_name=collection_name, data=rows)
            return res
        finally:
            vbase.close()


    def search(
        self,
        query: Union[str, VngInput],
        collection_name: str,
        limit: int = 10,
        vng_task: Union[EmbeddingTask, int, str] = EmbeddingTask.QUERY,
        output_fields: Optional[List[str]] = None,
        search_params: Optional[Dict] = None,
        vbase_config: Optional[VBaseConfig] = None,
    ) -> List[Dict[str, Any]]:
        """
        Embeds a query string and searches in VBase.
        
        Args:
            query: The search query text or VngInput.
            collection_name: Target VBase collection.
            limit: Number of results to return.
            vng_task: VNG task type (e.g. EMBED_TASK_QUERY).
            dim: Optional dimensionality for embedding.
            output_fields: List of fields to return from Milvus.
            search_params: Extra search parameters for Milvus.
            vbase_config: Optional config override for VBase connection.
        """
        # 1. Embed (Sync)
        vng = self._client.vng.connect()
        try:
            # embed returns list of lists, we take the first
            embeddings = vng.embed(
                inputs=[query],
                task=vng_task,
                dim=self.dim
            )
            if not embeddings:
                return []
            query_vector = embeddings[0]
        finally:
            vng.close()

        # 2. Search (Sync)
        vbase = self._client.vbase.connect(config=vbase_config)
        try:
            results = vbase.search(
                collection_name=collection_name,
                data=[query_vector],
                limit=limit,
                output_fields=output_fields,
                search_params=search_params
            )
            # Milvus returns list of lists (one per query). We only have one query.
            if results and len(results) > 0:
                out = []
                for hit in results[0]:
                    hit_dict = getattr(hit, "to_dict", lambda: hit if isinstance(hit, dict) else {})()
                    if not hit_dict and hasattr(hit, "entity"):
                         hit_dict = hit.entity.to_dict()
                         hit_dict["id"] = hit.id
                         hit_dict["score"] = hit.score
                    out.append(hit_dict)
                return out
            return []
        finally:
            vbase.close()

    def close(self):
        pass
