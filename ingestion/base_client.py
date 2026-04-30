"""Base API client for handling HTTP requests with retries."""

import asyncio
import logging
import httpx


logging.basicConfig(
    filename="nomad.log",
    level=logging.INFO,
    format='%(asctime)s: %(levelname)s: %(message)s'
)


class BaseAPIClient():
    """
    The BaseAPIClient is a base class for API clients.
    Provides GET requests with retry logic.
    """
    def __init__(self, base_url: str, headers: dict | None = None):
        self.base_url = base_url
        self.headers = headers or {}

    async def get(self, endpoint: str, params: dict | None = None) -> dict:
        """
        Basic fetc function. It can be built upon if the API
        requires more parameters or customization
        """
        url = f"{self.base_url}{endpoint}"
        for attempt in range(3):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        url,
                        params=params or {},
                        headers=self.headers,
                        timeout=10)
                    if response.status_code in (429, 500):
                        logging.error("%s", response.raise_for_status)
                        await asyncio.sleep(2 ** attempt)
                        continue
                    response.raise_for_status()
                    return response.json()
            except httpx.RequestError as e:
                logging.error("Request failed: %s", e)
                if attempt == 2:
                    logging.error("Request failed after 3 attempts: %s - %s",
                                  url,
                                  e
                                  )
                    return {}
        return {}
