from tests.conftest import REVIEW_BODY, make_bin


def test_feed_and_stats(client, register, auth_header, promote):
    register("w1@t.kz", "feed_user1")
    register("w2@t.kz", "feed_user2")
    register("mod@t.kz", "mod_bek")
    promote("mod@t.kz", "moderator")
    headers = auth_header("w1@t.kz")
    company_id = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Feed Test LLP"},
        headers=headers,
    ).json()["id"]

    review_id = client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 3, "body": REVIEW_BODY},
        headers=headers,
    ).json()["id"]
    client.post(
        f"/companies/{company_id}/complaints",
        json={
            "category": "salary_fraud",
            "stage": "interview",
            "source_type": "instagram",
            "advertised_salary": 700_000,
            "actual_salary": 150_000,
            "body": REVIEW_BODY,
        },
        headers=auth_header("w2@t.kz"),
    )

    items = client.get("/feed").json()
    assert len(items) == 2
    # Жаңасы бірінші: шағым отзывтан кейін жасалды
    assert items[0]["type"] == "complaint"
    assert items[0]["salary_diff_percent"] == -79
    assert items[0]["company_name"] == "Feed Test LLP"
    assert items[1]["type"] == "review"
    assert items[1]["overall_score"] == 3

    stats = client.get("/stats").json()
    assert stats == {"companies": 1, "reviews": 1, "complaints": 1}

    # Жасырылған контент лентадан да, статистикадан да шығады
    client.post(
        f"/moderation/reviews/{review_id}/hide",
        json={"reason": "Dalel suralganga deiin zhasyryldy"},
        headers=auth_header("mod@t.kz"),
    )
    assert len(client.get("/feed").json()) == 1
    assert client.get("/stats").json()["reviews"] == 0
