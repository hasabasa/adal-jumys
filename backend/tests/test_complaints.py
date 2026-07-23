from tests.conftest import REVIEW_BODY, make_bin


def _setup(client, register, auth_header) -> tuple[str, dict]:
    register("w@t.kz", "worker_01")
    headers = auth_header("w@t.kz")
    company_id = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Shagym Test LLP"},
        headers=headers,
    ).json()["id"]
    return company_id, headers


def test_salary_fraud_diff(client, register, auth_header):
    company_id, headers = _setup(client, register, auth_header)
    created = client.post(
        f"/companies/{company_id}/complaints",
        json={
            "category": "salary_fraud",
            "stage": "interview",
            "source_type": "instagram",
            "advertised_salary": 700_000,
            "actual_salary": 150_000,
            "body": REVIEW_BODY,
        },
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["salary_diff_percent"] == -79


def test_salary_fraud_requires_both_salaries(client, register, auth_header):
    company_id, headers = _setup(client, register, auth_header)
    response = client.post(
        f"/companies/{company_id}/complaints",
        json={
            "category": "salary_fraud",
            "stage": "call",
            "source_type": "hh",
            "body": REVIEW_BODY,
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_discrimination_category_requires_block(client, register, auth_header):
    company_id, headers = _setup(client, register, auth_header)
    without_block = client.post(
        f"/companies/{company_id}/complaints",
        json={
            "category": "discrimination",
            "stage": "interview",
            "source_type": "instagram",
            "body": REVIEW_BODY,
        },
        headers=headers,
    )
    assert without_block.status_code == 422
    with_block = client.post(
        f"/companies/{company_id}/complaints",
        json={
            "category": "discrimination",
            "stage": "interview",
            "source_type": "instagram",
            "body": REVIEW_BODY,
            "discrimination": [{"kind": "language", "form": "vacancy_text"}],
        },
        headers=headers,
    )
    assert with_block.status_code == 201


def test_new_discrimination_and_harassment_kinds(client, register, auth_header):
    """Кеңейтілген түрлер: жүктілік (кемсіту-тобы) мен бопсалау (қысым-тобы)."""
    company_id, headers = _setup(client, register, auth_header)
    response = client.post(
        f"/companies/{company_id}/complaints",
        json={
            "category": "discrimination",
            "stage": "interview",
            "source_type": "whatsapp",
            "body": REVIEW_BODY,
            "discrimination": [
                {"kind": "pregnancy", "form": "interview"},
                {"kind": "extortion", "form": "at_work"},
            ],
        },
        headers=headers,
    )
    assert response.status_code == 201
    kinds = [d["kind"] for d in response.json()["discrimination"]]
    assert kinds == ["pregnancy", "extortion"]


def test_stats(client, register, auth_header):
    company_id, headers = _setup(client, register, auth_header)
    client.post(
        f"/companies/{company_id}/complaints",
        json={
            "category": "ghost_vacancy",
            "stage": "call",
            "source_type": "hh",
            "body": REVIEW_BODY,
        },
        headers=headers,
    )
    client.post(
        f"/companies/{company_id}/complaints",
        json={
            "category": "discrimination",
            "stage": "interview",
            "source_type": "whatsapp",
            "body": REVIEW_BODY,
            "discrimination": [
                {"kind": "language", "form": "interview"},
                {"kind": "age", "form": "vacancy_text"},
            ],
        },
        headers=headers,
    )
    stats = client.get(f"/companies/{company_id}/complaints/stats").json()
    assert stats["total"] == 2
    assert stats["by_category"] == {"ghost_vacancy": 1, "discrimination": 1}
    assert stats["by_discrimination_kind"] == {"language": 1, "age": 1}
