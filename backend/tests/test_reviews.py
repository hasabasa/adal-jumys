import asyncio

from sqlalchemy import update

from app.db.session import async_session
from app.models import Review
from tests.conftest import REVIEW_BODY, make_bin


def _make_company(client, headers) -> str:
    response = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Reiting Test LLP"},
        headers=headers,
    )
    return response.json()["id"]


def test_create_and_list(client, register, auth_header):
    register("w@t.kz", "worker_01")
    headers = auth_header("w@t.kz")
    company_id = _make_company(client, headers)
    created = client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 3, "score_salary_timeliness": 2, "body": REVIEW_BODY},
        headers=headers,
    )
    assert created.status_code == 201
    listed = client.get(f"/companies/{company_id}/reviews").json()
    assert len(listed) == 1
    assert listed[0]["author_pseudonym"] == "worker_01"
    assert listed[0]["verification_status"] == "unverified"


def test_one_review_per_company(client, register, auth_header):
    register("w@t.kz", "worker_01")
    headers = auth_header("w@t.kz")
    company_id = _make_company(client, headers)
    payload = {"overall_score": 3, "body": REVIEW_BODY}
    assert (
        client.post(f"/companies/{company_id}/reviews", json=payload, headers=headers).status_code
        == 201
    )
    assert (
        client.post(f"/companies/{company_id}/reviews", json=payload, headers=headers).status_code
        == 409
    )


def test_company_role_cannot_review(client, register, auth_header):
    register("w@t.kz", "worker_01")
    register("hr@t.kz", "hr_account", role="company")
    company_id = _make_company(client, auth_header("w@t.kz"))
    response = client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 3, "body": REVIEW_BODY},
        headers=auth_header("hr@t.kz"),
    )
    assert response.status_code == 403


def test_short_body_rejected(client, register, auth_header):
    register("w@t.kz", "worker_01")
    headers = auth_header("w@t.kz")
    company_id = _make_company(client, headers)
    response = client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 3, "body": "qysqa"},
        headers=headers,
    )
    assert response.status_code == 422


def test_rating_bayesian_math(client, register, auth_header):
    """docs/rating.md формуласымen қолмен есептелген мәндер."""
    register("u1@t.kz", "user_bir")
    register("u2@t.kz", "user_eki")
    headers = auth_header("u1@t.kz")
    company_id = _make_company(client, headers)
    client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 2, "body": REVIEW_BODY},
        headers=headers,
    )
    client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 8, "body": REVIEW_BODY},
        headers=auth_header("u2@t.kz"),
    )
    # Екі верифицирленбеген (w=0.4): (0.4*2 + 0.4*8 + 5*5) / (0.8+5) = 5.0
    rating = client.get(f"/companies/{company_id}/rating").json()
    assert rating["rating"] == 5.0
    assert rating["review_count"] == 2

    async def _verify_low_score():
        async with async_session() as db:
            await db.execute(
                update(Review)
                .where(Review.overall_score == 2)
                .values(verification_status="verified")
            )
            await db.commit()

    asyncio.run(_verify_low_score())
    # Верифицирленген 2 (w=1.0) + верифицирленбеген 8 (w=0.4): 30.2/6.4 = 4.7
    rating = client.get(f"/companies/{company_id}/rating").json()
    assert rating["rating"] == 4.7
    assert rating["verified_count"] == 1


def test_problems_checklist(client, register, auth_header):
    """docs/categories.md чеклисті: жарамдылары сақталады, белгісізі 422."""
    register("w@t.kz", "worker_01")
    headers = auth_header("w@t.kz")
    company_id = _make_company(client, headers)
    created = client.post(
        f"/companies/{company_id}/reviews",
        json={
            "overall_score": 2,
            "body": REVIEW_BODY,
            "problems": ["unpaid_salary", "no_contract", "illegal_fines"],
        },
        headers=headers,
    )
    assert created.status_code == 201
    listed = client.get(f"/companies/{company_id}/reviews").json()
    assert sorted(listed[0]["problems"]) == [
        "illegal_fines",
        "no_contract",
        "unpaid_salary",
    ]

    register("w2@t.kz", "worker_02")
    invalid = client.post(
        f"/companies/{company_id}/reviews",
        json={
            "overall_score": 2,
            "body": REVIEW_BODY,
            "problems": ["belgisiz_kategoria"],
        },
        headers=auth_header("w2@t.kz"),
    )
    assert invalid.status_code == 422


def test_discrimination_block(client, register, auth_header):
    register("w@t.kz", "worker_01")
    headers = auth_header("w@t.kz")
    company_id = _make_company(client, headers)
    created = client.post(
        f"/companies/{company_id}/reviews",
        json={
            "overall_score": 2,
            "body": REVIEW_BODY,
            "discrimination": [
                {"kind": "language", "form": "at_work", "description": "Eskertu berdi"}
            ],
        },
        headers=headers,
    )
    assert created.status_code == 201
    listed = client.get(f"/companies/{company_id}/reviews").json()
    assert listed[0]["discrimination"][0]["kind"] == "language"
