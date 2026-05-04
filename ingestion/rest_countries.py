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

    def parse_countries(self, record: dict) -> dict | None:
        """
        Parse a single raw country record into a clean flat dict.
        Separated from fetch so it's easy to unit test independently.
        """
        capital = record.get("capital", [])
        capital_list = capital[0] if capital else None
        border_countries = list(record.get("borders", []))
        border_list = ", ".join(border_countries
                                ) if border_countries else None
        languages_dict = list(record.get("languages", {}).values())
        languages_list = ", ".join(languages_dict
                                   ) if languages_dict else None
        currencies_dict = record.get("currencies", {})
        currency_names = ", ".join(
            details.get("name", "code")
            for code, details in currencies_dict.items()
        ) if currencies_dict else None
        lat = record.get("latlng", {})[0]
        long = record.get("latlng", {})[1]

        return {
            "official_name": record.get("name", {}).get("official"),
            "iso_code": record.get("cca3"),
            "capital_city": capital_list,
            "lat": lat,
            "lng": long,
            "bordering_countries": border_list,
            "border_count": len(border_countries) if border_countries else 0,
            "languages": languages_list,
            "language_count": len(languages_dict) if languages_dict else None,
            "currencies": currency_names,
        }

    async def fetch_all(self):
        """Fetch all countries from the API."""
        response = await self.get(
            "/v3.1/all",
            params={
                "fields":
                "name,capital,currencies,cca3,borders,latlng,languages"
            }
        )
        if not response or not isinstance(response, list):
            return []
        return [self.parse_countries(record) for record in response]


async def main():
    """
    Run the client and return fetched country data.
    """
    import json
    client = RestCountries()
    data = await client.fetch_all()
    if data is not None:
        print(json.dumps(data[:5], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
