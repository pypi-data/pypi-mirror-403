__version__ = "0.0.7"

from fastapi_nacos.exception import ServiceRegistryConfigError
from fastapi_nacos.manager.fastapi_nacos_manager import FastApiNacos


__all__ = [
    "FastApiNacos",
    "ServiceRegistryConfigError"
]