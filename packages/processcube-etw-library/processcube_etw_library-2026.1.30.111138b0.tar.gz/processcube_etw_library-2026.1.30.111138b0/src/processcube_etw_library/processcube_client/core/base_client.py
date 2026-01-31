import asyncio
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)


def run_async_in_sync_context(coro):
    """Run an async coroutine in a synchronous context, compatible with Python 3.10+

    This function handles the proper creation and management of event loops
    for running async code from sync code. It's compatible with nested event loops
    (e.g., in Jupyter notebooks when nest_asyncio is applied).

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine
    """
    try:
        # Try to get the running loop (will work in async context)
        loop = asyncio.get_running_loop()
        # If we're here, we're already in an async context - this shouldn't happen
        # in normal sync-to-async transitions but can happen with nest_asyncio
        raise RuntimeError("Cannot use run_async_in_sync_context from an async context")
    except RuntimeError:
        # No running loop - we're in a sync context, which is what we want
        pass

    # Try to get or create an event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
        if loop.is_running():
            # Loop is running but we're not in it - this can happen with nest_asyncio
            # In this case, we need to schedule the coroutine on the existing loop
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()
    except RuntimeError:
        # No event loop or it's closed - create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Run the coroutine
    try:
        result = loop.run_until_complete(coro)
        return result
    finally:
        # Don't close the loop if it was already set as the event loop for this thread
        # This allows it to be reused in subsequent calls
        pass


class BaseClient:

    def __init__(self, url, session=None, identity=None):
        self._url = url
        self._session = session

        if identity is None:
            self._identity = {"token": "ZHVtbXlfdG9rZW4="}
        else:
            self._identity = identity

    async def __aenter__(self):
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        await self.close() 

    async def close(self):
        if self._session:
            await self._session.close()

    async def do_get(self, path, options={}):
        headers = self.__get_default_headers()
        headers.update(options.get('headers', {}))
        headers.update(self.__get_auth_headers())

        request_url = f"{self._url}{path}"

        async with aiohttp.ClientSession() as session:

            current_session = self._session if self._session else session

            async with current_session.get(request_url, headers=headers) as response:
                response.raise_for_status()
                if response.status == 200:
                    return await response.json()

    async def do_delete(self, path, options={}):
        headers = self.__get_default_headers()
        headers.update(options.get('headers', {}))
        headers.update(self.__get_auth_headers())

        request_url = f"{self._url}{path}"

        async with aiohttp.ClientSession() as session:

            current_session = self._session if self._session else session

            async with current_session.delete(request_url, headers=headers) as response:
                response.raise_for_status()
                if response.status == 200:
                    return await response.json()

    async def do_post(self, path, payload, options={}):
        headers = self.__get_default_headers()
        headers.update(options.get('headers', {}))
        headers.update(self.__get_auth_headers())

        request_url = f"{self._url}{path}"

        logger.debug(f"post request to {request_url} with json payload {payload}")

        async with aiohttp.ClientSession() as session:

            current_session = self._session if self._session else session

            async with current_session.post(request_url, json=payload, headers=headers) as response:
                logger.debug(f"handle response {response.status}")
                response.raise_for_status()
                if response.status in [200, 201, 202]:
                    return await response.json()
                elif response.status == 204:
                    return ""
                else:
                    raise Exception(f"TODO: need a better error {response.status}")
    
    async def do_put(self, path, payload, options={}):
        headers = self.__get_default_headers()
        headers.update(options.get('headers', {}))
        headers.update(self.__get_auth_headers())

        request_url = f"{self._url}{path}"

        logger.debug(f"put request to {request_url} with json payload {payload}")

        async with aiohttp.ClientSession() as session:

            current_session = self._session if self._session else session

            async with current_session.put(request_url, json=payload, headers=headers) as response:
                logger.debug(f"handle response {response.status}")
                response.raise_for_status()
                if response.status in [200, 201, 202]:
                    return await response.json()
                elif response.status == 204:
                    return ""
                else:
                    raise Exception(f"TODO: need a better error {response.status}")
    
    async def get_serverinfo(self):
        return await self.do_get('/atlas_engine/api/v1/info')

    def __get_auth_headers(self):
        identity = self.__get_identity()
        token = identity['token']
        return {'Authorization': 'Bearer {}'.format(token)}

    def __get_default_headers(self):
        return {'Content-Type': 'application/json'}

    def __get_identity(self):
        identity = self._identity

        if callable(self._identity):
            identity = self._identity()

        return identity
            
