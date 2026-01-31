import logging

from ..core import base_client

logger = logging.getLogger(__name__)


class ProcessInstanceClient(base_client.BaseClient):

    def __init__(self, url, session=None, identity=None):
        super(ProcessInstanceClient, self).__init__(url, session, identity)

    def terminate(self, process_instance_id):

        async def _terminate():
            url = f"/atlas_engine/api/v1/process_instances/{process_instance_id}/terminate"
            return await self.do_put(url, {})

        logger.info(f"Connection to process engine at url '{self._url}'.")
        logger.info(f"Terminate the process-instance '{process_instance_id}'.")

        return base_client.run_async_in_sync_context(_terminate())

    def retry(self, process_instance_id):

        async def _retry():
            url = f"/atlas_engine/api/v1/process_instances/{process_instance_id}/retry"
            return await self.do_put(url, {})

        logger.info(f"Retry process instance '{process_instance_id}' for atlas engine at url '{self._url}'.")

        return base_client.run_async_in_sync_context(_retry())
