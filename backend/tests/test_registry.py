import asyncio

from app.main import app as fastapi_app
from app.scripts.import_companies import import_csv
from app.services.registry import RegistryInfo, get_registry, parse_item
from tests.conftest import make_bin


def test_parse_item_ignores_director_pii():
    """data.egov.kz жазбасындағы director (адам аты-жөні) ешқашан алынбайды."""
    item = {
        "namekz": '"Kaspi Bank" акционерлік қоғамы',
        "nameru": 'Акционерное общество "Kaspi Bank"',
        "addresskz": "050013, АЛМАТЫ ҚАЛАСЫ, КӨШЕСІ НАУРЫЗБАЙ БАТЫР, д. 154А",
        "bin": "971240001315",
        "director": "ЖЕКЕ АДАМНЫҢ АТЫ-ЖӨНІ",
        "datereg": "1997-12-04",
    }
    info = parse_item(item, "971240001315")
    assert info.name == '"Kaspi Bank" акционерлік қоғамы'
    assert info.address.startswith("050013")
    assert "АТЫ-ЖӨНІ" not in str(info)


class FakeRegistry:
    async def lookup(self, company_bin: str) -> RegistryInfo | None:
        return RegistryInfo(
            bin=company_bin, name="Kaspi Bank AQ", oked="64191", city="Алматы"
        )


def test_lookup_with_registry(client):
    fastapi_app.dependency_overrides[get_registry] = lambda: FakeRegistry()
    try:
        response = client.get(f"/companies/lookup/{make_bin('12345678901')}")
        assert response.status_code == 200
        assert response.json()["name"] == "Kaspi Bank AQ"
    finally:
        fastapi_app.dependency_overrides.pop(get_registry)


def test_lookup_invalid_bin(client):
    bad_bin = next(
        f"12345678901{d}"
        for d in range(10)
        if f"12345678901{d}" != make_bin("12345678901")
    )
    assert client.get(f"/companies/lookup/{bad_bin}").status_code == 422


def test_lookup_without_registry_returns_404(client):
    # Әдепкі NullRegistryClient: реестр қосылмаған, қолмен енгізу ұсынылады
    assert client.get(f"/companies/lookup/{make_bin('12345678901')}").status_code == 404


def test_import_csv(client, tmp_path):
    valid_one = make_bin("11111111111")
    valid_two = make_bin("22222222222")
    csv_file = tmp_path / "top.csv"
    csv_file.write_text(
        "bin,name,city,address,oked\n"
        f"{valid_one},Kaspi Bank AQ,Алматы,Наурызбай батыра 154,64191\n"
        f"{valid_two},Magnum Cash&Carry ЖШС,Алматы,,47111\n"
        f"{valid_one},Qaita Import LLP,,,\n"
        "123,Qate BSN LLP,,,\n",
        encoding="utf-8",
    )
    stats = asyncio.run(import_csv(csv_file))
    assert stats == {"created": 2, "skipped_existing": 1, "invalid_bin": 1}

    found = client.get("/companies?search=Kaspi").json()
    assert len(found) == 1
    assert found[0]["source"] == "registry_import"

    # Қайта жүргізу қауіпсіз (идемпотентті)
    stats = asyncio.run(import_csv(csv_file))
    assert stats["created"] == 0
    assert stats["skipped_existing"] == 3
