"""API class for ingesting weather data from Open-Meteo"""

from base_client import BaseAPIClient
import asyncio
import logging

logging.basicConfig(
    filename="nomad.log",
    level=logging.INFO,
    format='%(asctime)s: %(levelname)s: %(message)s'
)


class OpenMeteo(BaseAPIClient):
    """
    Inherits BaseAPIClient retry logic.
    Fetches current weather and daily max/min for a given coordinate.
    """
    def __init__(self):
        super().__init__("https://api.open-meteo.com")

    async def fetch_weather(self, lat: float, lon: float,
                            country_code: str) -> dict:
        """
        Fetch weather for a single coordinate.
        country_code is passed through so the result stays
        identifiable after gather() merges everything.
        Fetch daily weather forecast for a single country
        """
        response = await self.get(
            "/v1/forecast?",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "uv_index_max,temperature_2m_max,temperature_2m_min",
                "current": "temperature_2m,precipitation,wind_speed_10m",
                "timezone": "auto",
                "forecast_days": 1
            }
            )
        if not response or not isinstance(response, dict):
            if not response or not isinstance(response, dict):
                logging.warning("Unexpected response for %s - %s - %s",
                                country_code,
                                lat,
                                lon)
                return {"country_code": country_code, "error": True}

        current = response.get("current", {})
        daily = response.get("daily", {})

        return {
            "country_code": country_code,
            "temperature": current.get("temperature_2m"),
            "precipitation": current.get("precipitation"),
            "wind_speed": current.get("wind_speed_10m"),
            "uv_index": daily.get("uv_index_max", [None])[0],
            "min_temp": daily.get("temperature_2m_min", [None])[0],
            "max_temp": daily.get("temperature_2m_max", [None])[0]
            }

    async def fetch_all_countries(self,
                                  locations: list[dict]) -> list[dict] | None:
        """
            Fetch weather for all countries concurrently.

            `locations` is a list of dicts from dim_locations:
                [{"country_code": "NGA", "lat": 6.52, "lon": 3.37}, ...]

            Returns a list of weather dicts, one per country.
            Failed fetches are logged and excluded from results.
            """
        tasks = [
            self.fetch_weather(loc["lat"], loc["lon"], loc["country_code"])
            for loc in locations
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        data = []
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Weather fetch failed: {result}")
                continue

            assert isinstance(result, dict)
            if result.get("error"):
                logging.warning(
                    f"Bad response for {result.get('country_code')}")
                continue

            if result not in data:
                data.append(result)

        return data


async def main():
    import json

    # Simulating what dim_locations will provide
    locations = [
        {"country_code": "DEU", "lat": 52.52, "lon": 13.41},
        {"country_code": "IND", "lat": 34.12, "lon": 76.34},
        {"country_code": "NGA", "lat":  6.52, "lon":  3.37},
    ]
    client = OpenMeteo()
    response = await client.fetch_all_countries(locations)
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
