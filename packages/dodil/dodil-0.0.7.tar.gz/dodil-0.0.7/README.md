# DODIL Python SDK

The **DODIL Python SDK** lets you interact with DODIL services from Python.

Currently supported services:
- **VNG**: multi-modal vector ingestion
- **VBase**: vector database (Milvus-backed)

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

---

## Documentation

- [Getting Started](docs/getting_started.md)
- [Multi-model Vector Embedding (VNG)](docs/vng/overview.md)
- [Vector Database (VBase)](docs/vbase/overview.md)

---

## Development

```bash
poetry install
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