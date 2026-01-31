import logging

from ..core import base_client

logger = logging.getLogger(__name__)


class FlowNodeInstanceClient(base_client.BaseClient):
    def __init__(self, url, session=None, identity=None):
        super(FlowNodeInstanceClient, self).__init__(url, session, identity)

    async def __trigger_message_event(self, event_name, process_instance_id=None):
        url = f"/atlas_engine/api/v1/messages/{event_name}/trigger"

        if process_instance_id is not None:
            url = f"{url}?processInstanceId={process_instance_id}"

        result = await self.do_post(url, {})

        return result

    def trigger_message_event(self, event_name, process_instance_id=None):
        logger.info(f"Connection to process engine at url '{self._url}'.")
        logger.info(f"Trigger message '{event_name}'.")

        return base_client.run_async_in_sync_context(
            self.__trigger_message_event(event_name, process_instance_id)
        )

    async def __trigger_signal_event(self, event_name):
        url = f"/atlas_engine/api/v1/signals/{event_name}/trigger"

        result = await self.do_post(url, {})

        return result

    def trigger_signal_event(self, event_name):
        logger.info(f"Connection to process engine at url '{self._url}'.")
        logger.info(f"Trigger signal '{event_name}'.")

        return base_client.run_async_in_sync_context(
            self.__trigger_signal_event(event_name)
        )
