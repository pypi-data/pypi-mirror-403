from typing import Optional
from yamlpyconfig.models import AlgorithmEnum
from yamlpyconfig import ConfigManager

class NacosConfig:

    def __init__(self, config_dir: Optional[str] = None,
                 crypto_algorithm: AlgorithmEnum | None = None, key: str = None):
        self._config_manager = ConfigManager(
            config_dir,
            crypto_algorithm=crypto_algorithm,
            key=key,
        )

    async def start(self):
        await self._config_manager.start()

    async def __aenter__(self):
        await self.start()
        return self


    async def stop(self):
        await self._config_manager.stop()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    @property
    def config(self):
        return self._config_manager.get_config()

    @property
    def config_manager(self):
        return self._config_manager