"""БСН бойынша компания-реестр lookup.

Дереккөз: data.egov.kz v4 API, gbd_ul датасеті (заңды тұлғалардың тіркеу
деректері). REGISTRY_API_URL/KEY конфигпен қосылады:
  REGISTRY_API_URL=https://data.egov.kz/api/v4/gbd_ul/v1

Конфиг бос болса NullRegistryClient: форма қолмен толтырылады.
"""

import json
from dataclasses import dataclass
from functools import lru_cache

import httpx2

from app.core.config import get_settings


@dataclass
class RegistryInfo:
    bin: str
    name: str
    oked: str | None = None
    city: str | None = None
    address: str | None = None


def parse_item(item: dict, company_bin: str) -> RegistryInfo | None:
    """Датасет жазбасынан ТЕК компания-өрістерді алады.

    director өрісі (басшының аты-жөні) - дербес дерек, ӘДЕЙІ оқылмайды:
    платформа жеке тұлға деректерін сақтамайды.
    """
    name = item.get("namekz") or item.get("nameru") or item.get("name")
    if not name:
        return None
    return RegistryInfo(
        bin=company_bin,
        name=name,
        oked=item.get("oked"),
        address=item.get("addresskz") or item.get("addressru"),
    )


class NullRegistryClient:
    async def lookup(self, company_bin: str) -> RegistryInfo | None:
        return None


class DataEgovRegistryClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def lookup(self, company_bin: str) -> RegistryInfo | None:
        params = {
            "apiKey": self.api_key,
            "source": json.dumps(
                {"size": 1, "query": {"match": {"bin": company_bin}}}
            ),
        }
        try:
            async with httpx2.AsyncClient(timeout=10) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx2.HTTPError, ValueError):
            # Реестр құласа платформа құламайды: lookup жай "табылмады" дейді
            return None
        if not isinstance(payload, list) or not payload:
            return None
        return parse_item(payload[0], company_bin)


@lru_cache
def get_registry() -> NullRegistryClient | DataEgovRegistryClient:
    settings = get_settings()
    if settings.registry_api_url:
        return DataEgovRegistryClient(
            settings.registry_api_url, settings.registry_api_key
        )
    return NullRegistryClient()
