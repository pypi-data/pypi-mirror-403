import logging

from ..core.base_client import BaseClient, run_async_in_sync_context

logger = logging.getLogger(__name__)


class AppInfoClient(BaseClient):
    def __init__(self, url, session=None, identity=None):
        super(AppInfoClient, self).__init__(url, session, identity)

    async def __get_info(self):
        url = f"/atlas_engine/api/v1/info"

        result = await self.do_get(url)

        return result

    def get_info(self):
        logger.info(f"Connection to atlas engine at url '{self._url}'.")
        logger.info(f"Get info of the atlas engine.")

        return run_async_in_sync_context(self.__get_info())

    async def __get_authority(self):
        url = f"/atlas_engine/api/v1/authority"

        result = await self.do_get(url)

        return result

    def get_authority(self):
        logger.info(f"Connection to atlas engine at url '{self._url}'.")
        logger.info(f"Get info of the authority of the atlas engine.")

        return run_async_in_sync_context(self.__get_authority())
