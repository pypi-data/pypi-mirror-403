from __future__ import annotations
import uuid
from typing import List, Optional, Dict, Any, Union
import asyncio
import concurrent.futures

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

from dodil.vng.vng_client import VngClient, VngInput, EmbeddingTask
from dodil.vbase import VBaseClient


class VSpace:
    """
    High-level structure combining VNG embedding and VBase storage/search.
    """
    def __init__(self, vbase: VBaseClient, vng: VngClient) -> None:
        self._vbase = vbase
        self._vng = vng
        self.dim = 2048
        self.collection_name: Optional[str] = None


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
        vbase = self._vbase
        
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
        self.collection_name = collection_name
        

        return collection_name


    def add(
        self,
        inputs: List[Union[str, VngInput]],
        ids: Optional[List[Union[int, str]]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        vng_task: Union[EmbeddingTask, int, str] = EmbeddingTask.INDEX, # Typed as Any/str to allow EmbedTask enum or string
        vector_field: str = "vector",
        text_field: str = "text",
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
            primary_field_name: Name of the primary key field if providing IDs (default: "id").
            batch_size: Number of items to process in one batch (default: 32).
            max_workers: Number of concurrent workers (default: 4).
        """
        if not inputs:
            return {"insert_count": 0}
            
        total = len(inputs)
        
        # If total is small enough, just run directly
        if total <= batch_size:
            return self._process_batch(
                inputs, ids, metadatas, 
                vng_task, vector_field, text_field, primary_field_name
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
                    b_in, b_id, b_meta, 
                    vng_task, vector_field, text_field, primary_field_name
                ) 
                for b_in, b_id, b_meta in batches
            ]
            
            iterator = concurrent.futures.as_completed(futures)
            if tqdm:
                iterator = tqdm(iterator, total=len(batches), desc="Creating Embeddings")
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
        ids: Optional[List[Union[int, str]]],
        metadatas: Optional[List[Dict[str, Any]]],
        vng_task: Union[EmbeddingTask, int, str],
        vector_field: str,
        text_field: str,
        primary_field_name: str,
    ) -> Dict[str, Any]:
        
        # Ensure thread has an event loop for grpc.aio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Normalize inputs to VngInput to access smart detection logic
        normalized_inputs = [VngInput.from_any(inp) for inp in inputs]

        # 1. Embed using VNG
        vng = self._vng
        embeddings_batch = vng.embed(
            inputs=normalized_inputs,
            task=vng_task,
            dim=self.dim,
            timeout=300.0, # Increased timeout for heavy batches
        )
        
        # 2. Prepare data for Milvus
        rows = []
        for i, (inp, chunks) in enumerate(zip(normalized_inputs, embeddings_batch)):
            if not chunks:
                continue

            # Iterate over all chunks for this input
            for chunk in chunks:
                vec = chunk["vector"]
                chunk_text = chunk.get("text")
                chunk_idx = chunk.get("index", 0)
                
                # Determine what to store in the text/source field
                # If VNG returned specific text segment, use it.
                # Otherwise fall back to input source string.
                val_str = chunk_text if chunk_text else inp.source

                row = {
                    text_field: val_str,
                    vector_field: vec,
                }
                
                # Handle Metadata
                meta_dict = {}
                # Add chunk info
                meta_dict["chunk"] = chunk_idx
                meta_dict["total_chunks"] = len(chunks)
                
                # Auto-populate 'type'/'kind' if not present
                if inp.kind_hint:
                     meta_dict["type"] = inp.kind_hint.lower()

                if metadatas and i < len(metadatas):
                    # Merge user-provided metadata
                    if metadatas[i]:
                        meta_dict.update(metadatas[i])
                
                # Handling ID strategies
                # If IDs are provided by user, they usually expect 1-1 mapping.
                # If we have multiple chunks, we can't reuse the Primary Key.
                # We store user_id as "parent_id" or "external_id" in metadata.
                # ONLY if there is exactly 1 chunk do we attempt to set the PK (if user provided ids).
                if ids is not None and i < len(ids):
                    user_id = ids[i]
                    if len(chunks) == 1:
                        row[primary_field_name] = user_id
                    else:
                        meta_dict["parent_id"] = user_id
                
                # Finalize meta field
                row["meta"] = meta_dict

                rows.append(row)

        # 3. Insert into VBase
        vbase = self._vbase
        if rows:
            res = vbase.insert(collection_name=self.collection_name, data=rows)
            return res
        return {"insert_count": 0}


    def search(
        self,
        query: Union[str, VngInput],
        limit: int = 10,
        vng_task: Union[EmbeddingTask, int, str] = EmbeddingTask.QUERY,
        output_fields: Optional[List[str]] = None,
        search_params: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Embeds a query string and searches in VBase.
        
        Args:
            query: The search query text or VngInput.
            collection_name: Target VBase collection.
            limit: Number of results to return.
            vng_task: VNG task type (e.g. EMBED_TASK_QUERY).
            output_fields: List of fields to return from Milvus.
            search_params: Extra search parameters for Milvus.
        """
        # 1. Embed (Sync)
        vng = self._vng
        # embed returns list of lists of chunks.
        # We assume the query is short enough to be 1 chunk, or we take the first.
        embeddings = vng.embed(
            inputs=[query],
            task=vng_task,
            dim=self.dim
        )
        if not embeddings or not embeddings[0]:
            return []
            
        # Extract vector from the first chunk of the first input
        query_chunk = embeddings[0][0]
        query_vector = query_chunk["vector"]

        # 2. Search (Sync)
        vbase = self._vbase
        results = vbase.search(
            collection_name=self.collection_name,
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

    def visualize(
        self,
        limit: int = 2000,
        n_clusters: Optional[int] = None,
        perplexity: int = 30,
        out: Optional[str] = None
    ) -> None:
        """
        Visualizes the embedding space in 2D using t-SNE and applies clustering.
        Requires 'scikit-learn', 'pandas', and 'plotly' installed.
        
        Args:
            collection_name: The VBase collection to visualize.
            limit: Maximum number of points to fetch for visualization.
            n_clusters: Number of clusters for KMeans. If None, it is estimated automatically.
            perplexity: t-SNE perplexity parameter.
            output_file: If provided, saves the interactive HTML plot to this path.
                         Otherwise, attempts to show it directly (e.g. in Jupyter).
        """
        try:
            import numpy as np
            import pandas as pd
            import plotly.express as px
            from sklearn.manifold import TSNE
            from sklearn.cluster import KMeans
        except ImportError as e:
            raise ImportError(
                "Visualization requires extra dependencies. "
                "Install them with: pip install scikit-learn pandas plotly"
            ) from e

        # 1. Fetch data from VBase
        # We query for all items (up to limit). assuming 'id' is int64 >= 0.
        # If your primary key is different, adjust the filter.
        print(f"Fetching up to {limit} vectors from '{self.collection_name}'...")
        res = self._vbase.raw.query(
            collection_name=self.collection_name,
            filter="id >= 0", 
            output_fields=["vector", "text", "meta", "id"],
            limit=limit
        )

        if not res:
            print(f"No data found in collection '{self.collection_name}'.")
            return

        # 2. Prepare Data
        ids = []
        vectors = []
        texts = []
        metas = []

        for item in res:
            vec = item.get("vector")
            if not vec: 
                continue
            
            vectors.append(vec)
            ids.append(item.get("id"))
            
            # Truncate text for display
            txt = item.get("text", "")
            if len(txt) > 200:
                txt = txt[:197] + "..."
            texts.append(txt)
            
            # Format meta as string for display
            m = item.get("meta") or {}
            # formatting nicely for hover
            import json
            try:
                m_str = json.dumps(m, indent=1)
            except Exception:
                m_str = str(m)
            metas.append(m_str)

        X = np.array(vectors)
        n_samples = len(X)
        if n_samples < 2:
            print("Not enough data points to visualize.")
            return

        print(f"Processing {n_samples} points...")

        # 3. Dimensionality Reduction (t-SNE)
        # Perplexity must be less than n_samples
        safe_perplexity = min(perplexity, max(1, n_samples - 1))
        
        tsne = TSNE(
            n_components=2, 
            perplexity=safe_perplexity, 
            random_state=42, 
            init='pca', 
            learning_rate='auto'
        )
        projections = tsne.fit_transform(X)

        # 4. Clustering (KMeans)
        if n_clusters is None:
            # Heuristic: roughly sqrt(N) but capped at 10 to preserve partial color distinctiveness
            # and min 2 to actually show clustering.
            estimated = int(n_samples ** 0.5)
            n_clusters = max(2, min(estimated, 10))
            print(f"Auto-determining clusters: selected {n_clusters} clusters for {n_samples} points.")

        safe_clusters = min(n_clusters, n_samples)
        if safe_clusters < 1:
            safe_clusters = 1 # Fallback, though max(2, ...) above prevents this usually

        kmeans = KMeans(n_clusters=safe_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(projections)

        # 5. Visualization (Plotly)
        df = pd.DataFrame({
            'x': projections[:, 0],
            'y': projections[:, 1],
            'cluster': [f"Cluster {l}" for l in labels],
            'text': texts,
            'meta': metas,
            'id': ids
        })

        fig = px.scatter(
            df, 
            x='x', 
            y='y', 
            color='cluster',
            hover_data={
                'x': False, 
                'y': False, 
                'cluster': True, 
                'id': True, 
                'text': True,
                'meta': False # Handle meta manually via customdata to support multiline
            },
            title=f"Embedding Space: {self.collection_name} (t-SNE + KMeans)",
            template="plotly_dark",
            custom_data=['meta']
        )

        # Enhance hover to show metadata blocks clearly
        # Using <br> for newlines in hover
        fig.update_traces(
            hovertemplate=(
                "<b>Cluster:</b> %{marker.color}<br>"
                "<b>ID:</b> %{customdata[1]}<br>"  # id is auto-added to customdata by hover_data
                "<b>Text:</b> %{customdata[2]}<br>" # text is auto-added
                "<b>Meta:</b><br>%{customdata[0]}<extra></extra>" # manual meta from custom_data
            )
        )
        
        # NOTE: 'hover_data' behavior in px.scatter appends columns to customdata in order after any explicit custom_data arg?
        # Actually px.scatter handles custom_data slightly differently. 
        # Let's be safer and more explicit with update_traces data mapping or rely on px simple hover.
        # Re-doing the simple hover to avoid complex index matching issues:
        
        fig = px.scatter(
            df, x='x', y='y', color='cluster',
            hover_name='id', 
            hover_data=['text', 'meta'],
            title=f"Space: {self.collection_name} (t-SNE, {n_samples} points)",
            template="plotly_dark"
        )
        
        # Force multiline display for meta/text if possible, but basic hover is often standard line-based.
        # To truly support "click to check source", we rely on the interactive plot.
        
        if out:
            fig.write_html(out)
            print(f"Visualization saved to {out}")
        else:
            fig.show()

    def close(self):
        self._vbase.close()
        self._vng.close()


class VSpaceServiceHandle:
    """Lazy service handle for Space which combines VNG and VBase."""

    def __init__(
        self,
        vbase: VBaseClient,
        vng: VngClient,
    ) -> None:
        self._vbase = vbase
        self._vng = vng

    def connect(self) -> VSpace:
        """
        Create a bound VSpace instance using the pre-connected clients.
        """
        return VSpace(vbase=self._vbase, vng=self._vng)
