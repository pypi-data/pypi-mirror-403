# DODIL Python SDK

The **DODIL Python SDK** lets you interact with DODIL services from Python.

Currently supported services:

- **VNG**: multi-modal vector ingestion
- **VBase**: vector database (Milvus-backed)
- **VSpace**: integrated embedding + storage structure

---

## Install

```bash
pip install dodil
```

---

## Quick start

Create a client using a **service account**:

```python
from dodil import Client

c = Client(
    profile="staging",  # or "prod"
    service_account_id="...",
    service_account_secret="...",
)
```

VBase (connect + list collections):

```python
from dodil import VBaseConfig

vbase = c.vbase.connect(
    VBaseConfig(
        host="vbase-db-<id>.infra.dodil.cloud",
        port=443,
        scheme="https",
        db_name="db_<id>",
    )
)

print(vbase.list_collections())

vbase.close()
c.close()
```

## VSpace

For varied use cases involving embedding + storage, the SDK provides a **VSpace** structure. This allows you to embed texts via VNG and store/search them in VBase with single commands.

### 1) Initialize VSpace

```python
space = c.vspace.connect()
col_name = space.setup(dim=1024)  # Setup space with desired embedding dimension
```

### 2) Index data

```python
from dodil.vng import EmbeddingTask

space.add(
    data=[
        "apple",
        "banana",
        # Example: embedding an image from URL
        "https://example.com/cherry.jpg"
    ],
    ids=[1, 2, 3],  # Optional manually assigned IDs
    vng_task=EmbeddingTask.INDEX
)
```

### 3) Search data

```python
# Search with text
results = space.search(
    query="fruit",
    limit=5,
    vng_task=EmbeddingTask.QUERY,
    output_fields=["text", "id"]
)

print(f"Found {len(results)} results:")
for i, hit in enumerate(results):
    print(f"\nResult {i+1}:")
    print(f"  Score: {hit.get('distance'):.4f}")

```

## 4) Visualize

```python
space.visualize()
```

---

## Documentation

- [Tutorial](https://github.com/dodilio/sdk-dodil-python/blob/0.1/docs/tutorial.md)
- [Multi-model Vector Embedding (VNG)](https://github.com/dodilio/sdk-dodil-python/blob/0.1/docs/vng/overview.md)
- [Vector Database (VBase)](https://github.com/dodilio/sdk-dodil-python/blob/0.1/docs/vbase/overview.md)

## Examples

Check out the [examples/](https://github.com/dodilio/sdk-dodil-python/tree/0.1/examples) directory for more usage scenarios:

- [Index Dropbox](https://github.com/dodilio/sdk-dodil-python/blob/0.1/examples/index_dropbox.ipynb)
- [Index Google Drive](https://github.com/dodilio/sdk-dodil-python/blob/0.1/examples/index_google_drive.ipynb)

---

## Development

```bash
uv sync
pytest
```

---

## Contributing

We welcome issues and pull requests.

	–	Keep public APIs stable (prefer additive changes).
	–	Maintain backward compatibility where possible.
	-	Add tests for bug fixes and new features.
	-	Format and lint before opening a PR.

Project conventions

	-	Root client: Client
	-	Services are accessed through handles (e.g. client.vng, client.vbase).
	-	Bound service clients are created via .connect(...)