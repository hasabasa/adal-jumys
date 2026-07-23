from tests.conftest import REVIEW_BODY, make_bin

PDF_BYTES = b"%PDF-1.4 fake-contract-fragment"


def _setup(client, register, auth_header, promote) -> dict:
    register("w@t.kz", "worker_01")
    register("mod@t.kz", "mod_bek")
    promote("mod@t.kz", "moderator")
    worker = auth_header("w@t.kz")
    company_id = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Verif Test LLP"},
        headers=worker,
    ).json()["id"]
    review_id = client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 2, "body": REVIEW_BODY},
        headers=worker,
    ).json()["id"]
    return {
        "worker": worker,
        "moderator": auth_header("mod@t.kz"),
        "company_id": company_id,
        "review_id": review_id,
    }


def _submit(client, ctx) -> dict:
    response = client.post(
        f"/companies/{ctx['company_id']}/reviews/{ctx['review_id']}/verification",
        files={"file": ("shart.pdf", PDF_BYTES, "application/pdf")},
        headers=ctx["worker"],
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_submit_sets_pending(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    _submit(client, ctx)
    listed = client.get(f"/companies/{ctx['company_id']}/reviews").json()
    assert listed[0]["verification_status"] == "pending"


def test_double_submit_blocked(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    _submit(client, ctx)
    second = client.post(
        f"/companies/{ctx['company_id']}/reviews/{ctx['review_id']}/verification",
        files={"file": ("shart.pdf", PDF_BYTES, "application/pdf")},
        headers=ctx["worker"],
    )
    assert second.status_code == 409


def test_verification_file_never_public(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    evidence_id = _submit(client, ctx)["id"]
    # Жария файл-эндпоинт верификация-файлды ешқашан бермейді
    assert client.get(f"/evidence/{evidence_id}").status_code == 404
    # Жария отзыв-тізімінде де жоқ
    assert client.get(f"/companies/{ctx['company_id']}/reviews").json()[0]["evidence"] == []


def test_approve_deletes_file_and_verifies(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    evidence_id = _submit(client, ctx)["id"]

    queue = client.get("/moderation/verifications", headers=ctx["moderator"]).json()
    assert len(queue) == 1
    assert queue[0]["review_id"] == ctx["review_id"]

    approve = client.post(
        f"/moderation/verifications/{ctx['review_id']}/approve",
        json={"method": "employment_contract", "reason": "Enbek sharty fragmenti rastaldy"},
        headers=ctx["moderator"],
    )
    assert approve.status_code == 200

    listed = client.get(f"/companies/{ctx['company_id']}/reviews").json()
    assert listed[0]["verification_status"] == "verified"
    # Файл дереу өшірілді: модератордың өзі де енді көре алмайды
    preview = client.get(
        f"/moderation/evidence/{evidence_id}/file", headers=ctx["moderator"]
    )
    assert preview.status_code == 404
    # Кезек бос
    assert client.get("/moderation/verifications", headers=ctx["moderator"]).json() == []
    # Рейтинг верифицирленген салмаққа ауысты: (1.0*2 + 5*2)/(1.0+5) = 2.0
    rating = client.get(f"/companies/{ctx['company_id']}/rating").json()
    assert rating["verified_count"] == 1


def test_reject_deletes_file_and_marks_rejected(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    evidence_id = _submit(client, ctx)["id"]
    reject = client.post(
        f"/moderation/verifications/{ctx['review_id']}/reject",
        json={"method": "other", "reason": "Qujat oqylmaidy, rastau mumkin emes"},
        headers=ctx["moderator"],
    )
    assert reject.status_code == 200
    listed = client.get(f"/companies/{ctx['company_id']}/reviews").json()
    assert listed[0]["verification_status"] == "rejected"
    assert (
        client.get(
            f"/moderation/evidence/{evidence_id}/file", headers=ctx["moderator"]
        ).status_code
        == 404
    )


def test_decision_requires_pending(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    response = client.post(
        f"/moderation/verifications/{ctx['review_id']}/approve",
        json={"method": "other", "reason": "fail zhoq bolsa da approve"},
        headers=ctx["moderator"],
    )
    assert response.status_code == 409
