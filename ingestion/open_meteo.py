"""API class for ingesting weather data from open meteo"""

from base_client import BaseAPIClient
import asyncio


class OpenMeteo(BaseAPIClient):
    """
    This class inherits from the BaseAPIClient, and uses its retry logic.
    It's methods fetces the weather data from open meteo API
    """
    def __init__(self):
        super().__init__("https://api.open-meteo.com")

    async def fetch_weather(self, lat: float, lon: float) -> dict:
        """Fetch daily weather forecast for a single country"""
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
        return response


async def main():
    """
    OpenMeteo client call.
    Returns json data
    """
    import json
    client = OpenMeteo()
    data = await client.fetch_weather(52.52, 13.41)
    # return data
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
