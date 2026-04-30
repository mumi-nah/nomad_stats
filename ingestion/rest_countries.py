"""API class for ingesting the anchor data from Countries API"""

from base_client import BaseAPIClient
import asyncio


class RestCountries(BaseAPIClient):
    """
    This class inherits from the BaseAPIClient, so it uses the retry logic.
    It's methods fetces the countries data.
    """
    def __init__(self):
        super().__init__("https://restcountries.com")

    async def fetch_all(self):
        """Fetch all countries from the API."""
        return await self.get(
            "/v3.1/all",
            params={
                "fields":
                "name,capital,currencies,cca3,borders,latlng,languages"
            }
        )


async def main():
    """
    Run the client and return fetched country data.
    """
    # import json
    client = RestCountries()
    data = await client.fetch_all()
    return data
    # print(json.dumps(data[1], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
