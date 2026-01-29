__all__ = []

try:
    from .app import create_app

    __all__ = ["create_app"]
except ImportError:
    pass

from ._serializers import SerializerRegistry, FeatureRegistryId

__all__ = [*__all__, "SerializerRegistry", "FeatureRegistryId"]

__version__ = "0.3.4"
