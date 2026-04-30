"""API class for ingesting economy data from world bank"""

from base_client import BaseAPIClient
from datetime import datetime
import logging
import asyncio

logging.basicConfig(
    filename="nomad.log",
    level=logging.INFO,
    format='%(asctime)s: %(levelname)s: %(message)s'
)

INDICATORS = {
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "inflation_rate": "FP.CPI.TOTL.ZG",
    "electricity_access": "EG.ELC.ACCS.ZS",
    "total_pop": "SP.POP.TOTL",
}


class WorldBank(BaseAPIClient):
    """
    This class inherits from the BaseAPIClient, so it uses the retry logic.
    It's methods fetces the economy data from world bank API
    """
    def __init__(self):
        super().__init__("https://api.worldbank.org")

    async def fetch_indicator_all_countries(self, indicator_code: str) -> dict:
        """
        Fetch one indicator for ALL countries, handling pagination.
        Returns a dict keyed by ISO country code:
            { "NGA": {"value": 2065.1, "year": 2022},
        """
        current_year = datetime.now().year
        date_range = f"{current_year - 5}:{current_year}"

        raw = {}
        page = 1

        while True:
            response = await self.get(
                f"/v2/country/NGA/indicator/{indicator_code}",
                params={
                    "format": "json",
                    "per_page": 500,
                    "page": page,
                    "date": date_range,
                    }
                )
            if not response or len(response) < 2 or not response[1]:
                logging.info("bad response")
                break

            metadata = response[0]
            records = response[1]
            for record in records:
                iso_code = record.get("countryiso3code") or record.get(
                    "country", {}).get("id")
                value = record.get("value")
                year = record.get("date")

                if not iso_code or value is None:
                    continue

                if iso_code not in raw:
                    raw[iso_code] = []
                    raw[iso_code].append({
                        "value": value,
                        "year": int(year)
                    })
            total_pages = metadata.get("pages", 1)
            if page >= total_pages:
                break
            page += 1
        results = {}
        for iso_code, entries in raw.items():
            latest = max(entries, key=lambda x: x["year"])
            results[iso_code] = latest
        return results

    async def fetch_all_indicators(self) -> dict | None:
        """
        fetch all 4 indicators for all countries
        Returns a nested dict.
        """
        tasks = {
            name: self.fetch_indicator_all_countries(code)
            for name, code in INDICATORS.items()
        }
        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True
        )
        indicator_results = dict(zip(tasks.keys(), results))

        merged = {}
        for name, indicator_data in indicator_results.items():
            if isinstance(indicator_data, Exception):
                logging.info(
                    "Ingestion failed for %s - %s",
                    name,
                    indicator_data
                    )
                continue

            assert isinstance(indicator_data, dict)
            # if not isinstance (indicator_data, dict):
            for iso_code, payload in indicator_data.items():
                merged.setdefault(iso_code, {})[name] = payload
        return merged


async def main():
    """
    WorldBank client call.
    Returns json data
    """
    client = WorldBank()
    all_data = await client.fetch_all_indicators()
    return all_data


if __name__ == "__main__":
    asyncio.run(main())
