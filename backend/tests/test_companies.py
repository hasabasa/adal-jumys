from tests.conftest import make_bin


def test_create_and_get(client, register, auth_header):
    register("w@t.kz", "worker_01")
    headers = auth_header("w@t.kz")
    created = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Adal Contora LLP", "city": "Астана"},
        headers=headers,
    )
    assert created.status_code == 201
    company = client.get(f"/companies/{created.json()['id']}").json()
    assert company["name"] == "Adal Contora LLP"
    assert company["source"] == "user_created"


def test_invalid_bin_checksum(client, register, auth_header):
    register("w@t.kz", "worker_01")
    bad_bin = next(
        f"12345678901{d}"
        for d in range(10)
        if f"12345678901{d}" != make_bin("12345678901")
    )
    response = client.post(
        "/companies", json={"bin": bad_bin, "name": "Test LLP"}, headers=auth_header("w@t.kz")
    )
    assert response.status_code == 422


def test_duplicate_bin(client, register, auth_header):
    register("w@t.kz", "worker_01")
    headers = auth_header("w@t.kz")
    company_bin = make_bin("12345678901")
    client.post("/companies", json={"bin": company_bin, "name": "Birinshi LLP"}, headers=headers)
    duplicate = client.post(
        "/companies", json={"bin": company_bin, "name": "Ekinshi LLP"}, headers=headers
    )
    assert duplicate.status_code == 409


def test_requires_auth(client):
    response = client.post(
        "/companies", json={"bin": make_bin("12345678901"), "name": "Test LLP"}
    )
    assert response.status_code == 401


def test_search(client, register, auth_header):
    register("w@t.kz", "worker_01")
    headers = auth_header("w@t.kz")
    company_bin = make_bin("12345678901")
    client.post("/companies", json={"bin": company_bin, "name": "Zhaman Contora LLP"}, headers=headers)
    client.post(
        "/companies", json={"bin": make_bin("12345678902"), "name": "Adal Firma LLP"}, headers=headers
    )
    assert len(client.get("/companies?search=Zhaman").json()) == 1
    assert len(client.get(f"/companies?search={company_bin}").json()) == 1
    assert len(client.get("/companies").json()) == 2


def test_empty_rating(client, register, auth_header):
    register("w@t.kz", "worker_01")
    created = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Bos LLP"},
        headers=auth_header("w@t.kz"),
    )
    rating = client.get(f"/companies/{created.json()['id']}/rating").json()
    assert rating == {"rating": None, "review_count": 0, "verified_count": 0}
