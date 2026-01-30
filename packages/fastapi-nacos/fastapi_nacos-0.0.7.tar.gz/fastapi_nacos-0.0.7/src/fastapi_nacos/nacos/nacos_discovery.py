from typing import Optional

from aio_service_caller import ServiceManager, IServiceInterceptor
from yamlpyconfig import ConfigManager


# Project01/configs.py

class NacosDiscovery:
    def __init__(self, config_manager: ConfigManager,
                 interceptors: Optional[list[IServiceInterceptor]] = None,
                 **kwargs):
        self._service_manager = ServiceManager(config_manager=config_manager, interceptors=interceptors, **kwargs)

    @property
    def service_manager(self):
        return self._service_manager

    async def start(self):
        await self._service_manager.start()

    async def __aenter__(self):
        await self.start()
        return self


    async def stop(self):
        await self._service_manager.stop()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
