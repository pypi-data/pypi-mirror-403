from .client import Client
from .space import Space

# Services (optional convenience)
from .vng.vng_client import VngConfig
from .vbase.vbase_client import VBaseConfig

__all__ = [
    "Client",
    "Space",
    "VngConfig",
    "VBaseConfig"
]