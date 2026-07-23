from tests.conftest import REVIEW_BODY, make_bin


def test_helpful_toggle(client, register, auth_header):
    register("w@t.kz", "worker_01")
    register("w2@t.kz", "worker_02")
    worker = auth_header("w@t.kz")
    other = auth_header("w2@t.kz")
    company_id = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Vote Test LLP"},
        headers=worker,
    ).json()["id"]
    review_id = client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 3, "body": REVIEW_BODY},
        headers=worker,
    ).json()["id"]
    url = f"/companies/{company_id}/reviews/{review_id}/helpful"

    # Авторизациясыз болмайды
    assert client.post(url).status_code == 401

    # Дауыс беру -> қайтарып алу -> қайта беру (toggle)
    assert client.post(url, headers=other).json() == {"count": 1, "voted": True}
    assert client.post(url, headers=other).json() == {"count": 0, "voted": False}
    assert client.post(url, headers=other).json() == {"count": 1, "voted": True}

    # Екінші юзер қосылса 2 болады
    assert client.post(url, headers=worker).json()["count"] == 2

    # Тізімде санауыш көрінеді
    listed = client.get(f"/companies/{company_id}/reviews").json()
    assert listed[0]["helpful_count"] == 2
