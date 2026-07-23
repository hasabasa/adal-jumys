from tests.conftest import REVIEW_BODY, make_bin


def _setup(client, register, auth_header, promote) -> dict:
    register("w@t.kz", "worker_01")
    register("hr@t.kz", "hr_official", role="company")
    register("mod@t.kz", "mod_bek")
    promote("mod@t.kz", "moderator")
    worker = auth_header("w@t.kz")
    company_id = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Moderatsia LLP"},
        headers=worker,
    ).json()["id"]
    review_id = client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 3, "body": REVIEW_BODY},
        headers=worker,
    ).json()["id"]
    return {
        "worker": worker,
        "hr": auth_header("hr@t.kz"),
        "moderator": auth_header("mod@t.kz"),
        "company_id": company_id,
        "review_id": review_id,
    }


def test_regular_user_cannot_hide(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    response = client.post(
        f"/moderation/reviews/{ctx['review_id']}/hide",
        json={"reason": "zhai user zhasyrgysy keledi"},
        headers=ctx["worker"],
    )
    assert response.status_code == 403


def test_hide_unhide_and_public_log(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    hide = client.post(
        f"/moderation/reviews/{ctx['review_id']}/hide",
        json={"reason": "Dalelsiz aiyptau, avtordan dalel suraldy"},
        headers=ctx["moderator"],
    )
    assert hide.status_code == 200
    assert client.get(f"/companies/{ctx['company_id']}/reviews").json() == []

    # Ашық лог авторизациясыз көрінеді
    log = client.get("/moderation/log").json()
    assert log[0]["action"] == "hide"
    assert log[0]["actor_pseudonym"] == "mod_bek"

    double_hide = client.post(
        f"/moderation/reviews/{ctx['review_id']}/hide",
        json={"reason": "qaita zhasyru"},
        headers=ctx["moderator"],
    )
    assert double_hide.status_code == 409

    unhide = client.post(
        f"/moderation/reviews/{ctx['review_id']}/unhide",
        json={"reason": "Avtor dalel usyndy, rastaldy"},
        headers=ctx["moderator"],
    )
    assert unhide.status_code == 200
    assert len(client.get(f"/companies/{ctx['company_id']}/reviews").json()) == 1


def test_conflict_of_interest(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    client.post(
        f"/companies/{ctx['company_id']}/reviews",
        json={"overall_score": 5, "body": REVIEW_BODY},
        headers=ctx["moderator"],
    )
    response = client.post(
        f"/moderation/reviews/{ctx['review_id']}/hide",
        json={"reason": "endi zhasyrgym keledi"},
        headers=ctx["moderator"],
    )
    assert response.status_code == 403


def test_representative_flow_and_response(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    company_id, review_id = ctx["company_id"], ctx["review_id"]

    worker_request = client.post(
        f"/companies/{company_id}/representatives",
        json={"proof_method": "domain_email"},
        headers=ctx["worker"],
    )
    assert worker_request.status_code == 403

    request = client.post(
        f"/companies/{company_id}/representatives",
        json={"proof_method": "domain_email"},
        headers=ctx["hr"],
    )
    assert request.status_code == 201

    early_response = client.post(
        f"/companies/{company_id}/reviews/{review_id}/response",
        json={"body": "Rastausyz zhauap beremin dep otyrmyn"},
        headers=ctx["hr"],
    )
    assert early_response.status_code == 403

    queue = client.get("/moderation/representatives", headers=ctx["moderator"]).json()
    assert len(queue) == 1
    approve = client.post(
        f"/moderation/representatives/{queue[0]['id']}/approve",
        json={"reason": "Domen-email rastaldy"},
        headers=ctx["moderator"],
    )
    assert approve.status_code == 200

    response = client.post(
        f"/companies/{company_id}/reviews/{review_id}/response",
        json={"body": "Faktiler tekserildi, mәsele sheshildi"},
        headers=ctx["hr"],
    )
    assert response.status_code == 201
    listed = client.get(f"/companies/{company_id}/reviews").json()
    assert listed[0]["company_response"]["body"].startswith("Faktiler")

    duplicate = client.post(
        f"/companies/{company_id}/reviews/{review_id}/response",
        json={"body": "Tagy bir zhauap bergim keledi"},
        headers=ctx["hr"],
    )
    assert duplicate.status_code == 409
