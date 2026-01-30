class ServiceRegistryConfigError(Exception):
    """Raised when service registry configuration is missing or invalid."""
    pass


__all__ = [
    "ServiceRegistryConfigError",
]