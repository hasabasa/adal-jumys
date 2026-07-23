from tests.conftest import REVIEW_BODY, make_bin


def _company(client, headers) -> str:
    return client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Badge Test LLP"},
        headers=headers,
    ).json()["id"]


def _salary_complaint(client, company_id, headers):
    return client.post(
        f"/companies/{company_id}/complaints",
        json={
            "category": "salary_fraud",
            "stage": "interview",
            "source_type": "hh",
            "advertised_salary": 700_000,
            "actual_salary": 150_000,
            "body": REVIEW_BODY,
        },
        headers=headers,
    )


def test_salary_badge_needs_five_independent_authors(client, register, auth_header):
    """4 автор - бейдж жоқ; 5-автор келгенде бейдж жанады; бір автордың
    қайталауы саналмайды (тәуелсіздік = бөлек аккаунттар)."""
    for i in range(5):
        register(f"u{i}@t.kz", f"salaryuser_{i}")
    first = auth_header("u0@t.kz")
    company_id = _company(client, first)

    for i in range(4):
        _salary_complaint(client, company_id, auth_header(f"u{i}@t.kz"))
    assert client.get(f"/companies/{company_id}/badges").json() == []

    _salary_complaint(client, company_id, auth_header("u4@t.kz"))
    badges = client.get(f"/companies/{company_id}/badges").json()
    assert len(badges) == 1
    assert badges[0]["badge"] == "salary_not_confirmed"


def test_fines_badge_and_revoke_on_hide(client, register, auth_header, promote):
    """3 айыппұл-белгісі бар отзыв - бейдж; біреуі жасырылса - бейдж қайтарылады."""
    for i in range(3):
        register(f"f{i}@t.kz", f"finesuser_{i}")
    register("mod@t.kz", "mod_bek")
    promote("mod@t.kz", "moderator")
    first = auth_header("f0@t.kz")
    company_id = _company(client, first)

    review_ids = []
    for i in range(3):
        response = client.post(
            f"/companies/{company_id}/reviews",
            json={"overall_score": 2, "body": REVIEW_BODY, "problems": ["illegal_fines"]},
            headers=auth_header(f"f{i}@t.kz"),
        )
        review_ids.append(response.json()["id"])

    badges = client.get(f"/companies/{company_id}/badges").json()
    assert [b["badge"] for b in badges] == ["repeated_illegal_fines"]

    client.post(
        f"/moderation/reviews/{review_ids[0]}/hide",
        json={"reason": "Dalel zhetkiliksiz, avtordan suraldy"},
        headers=auth_header("mod@t.kz"),
    )
    assert client.get(f"/companies/{company_id}/badges").json() == []


def test_language_badge_counts_reviews_and_complaints(client, register, auth_header):
    """Тіл-кемсіту блоктары отзыв пен шағымнан бірге саналады (3 тәуелсіз автор)."""
    for i in range(3):
        register(f"l{i}@t.kz", f"languser_{i}")
    first = auth_header("l0@t.kz")
    company_id = _company(client, first)

    block = [{"kind": "language", "form": "interview"}]
    client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 2, "body": REVIEW_BODY, "discrimination": block},
        headers=auth_header("l0@t.kz"),
    )
    client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 3, "body": REVIEW_BODY, "discrimination": block},
        headers=auth_header("l1@t.kz"),
    )
    assert client.get(f"/companies/{company_id}/badges").json() == []

    client.post(
        f"/companies/{company_id}/complaints",
        json={
            "category": "discrimination",
            "stage": "interview",
            "source_type": "instagram",
            "body": REVIEW_BODY,
            "discrimination": block,
        },
        headers=auth_header("l2@t.kz"),
    )
    badges = client.get(f"/companies/{company_id}/badges").json()
    assert [b["badge"] for b in badges] == ["repeated_language_discrimination"]
