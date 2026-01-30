import asyncio
import logging
from functools import wraps
from typing import Optional, Any

from aio_service_caller import ServiceManager
from yamlpyconfig.models import AlgorithmEnum

from ..exception import ServiceRegistryConfigError
from ..nacos.nacos_config import NacosConfig
from ..nacos.nacos_discovery import NacosDiscovery

logger = logging.getLogger(__name__)

def singleton(cls):
    instance = {}
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instance:
            instance[cls] = cls(*args, **kwargs)
        return instance[cls]
    return get_instance

@singleton
class FastApiNacos:

    def __init__(self, config_dir: Optional[str] = None,
                 crypto_algorithm: AlgorithmEnum | None = None, key: str = None,
                 **kwargs):
        self._nacos_config = NacosConfig(config_dir, crypto_algorithm, key)
        self._discovery = None
        self._kwargs = kwargs

    async def start(self):
        config = self._nacos_config.config
        tasks = []
        if "app-registry" in config and "nacos" in config["app-registry"]:
            if "new_thread" not in self._kwargs:
                self._kwargs["new_thread"] = False
            self._discovery = NacosDiscovery(config_manager=self._nacos_config.config_manager,
                                             interceptors=[], **self._kwargs)
            task_service_registry = asyncio.create_task(self._discovery.start())
            task_service_registry.add_done_callback(lambda t: logger.error(f"service registry error: {t.exception()}") if t.exception() else None)
            tasks.append(task_service_registry)
        else:
            logger.warning("No app-registry configuration found, so the service manager will be None.")

        task_config = asyncio.create_task(self._nacos_config.start())
        task_config.add_done_callback(lambda t: logger.error(f"get nacos config error: {t.exception()}") if t.exception() else None)
        tasks.append(task_config)
        await asyncio.gather(*tasks, return_exceptions=True)

    async def __aenter__(self):
        await self.start()
        return self

    async def stop(self):
        tasks = []
        task_config = asyncio.create_task(self._nacos_config.stop())
        task_config.add_done_callback(lambda t: logger.error(f"nacos config stop error: {t.exception()}") if t.exception() else None)
        tasks.append(task_config)
        if self._discovery:
            task_service_registry = asyncio.create_task(self._discovery.stop())
            task_service_registry.add_done_callback(lambda t: logger.error(f"service discovery stop error: {t.exception()}") if t.exception() else None)
            tasks.append(task_service_registry)
        await asyncio.gather(*tasks, return_exceptions=True)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


    @property
    def service_manager(self) -> Optional[ServiceManager]:
        """如果配置中存在app-registry.nacos的相关配置则返回ServiceManager对象，否则将抛出ServiceRegistryConfigError"""
        if self._discovery:
            return self._discovery.service_manager
        else:
            message = (
                "No app-registry configuration found; "
                "service manager cannot be initialized."
            )
            raise ServiceRegistryConfigError(message)

    @property
    def config(self) -> dict[str, Any]:
        return self._nacos_config.config