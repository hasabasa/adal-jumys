from tests.conftest import REVIEW_BODY, make_bin


def _setup(client, register, auth_header, promote) -> dict:
    register("w@t.kz", "worker_01")
    register("w2@t.kz", "worker_02")
    register("mod@t.kz", "mod_bek")
    promote("mod@t.kz", "moderator")
    worker = auth_header("w@t.kz")
    company_id = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Comment Test LLP"},
        headers=worker,
    ).json()["id"]
    review_id = client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 3, "body": REVIEW_BODY},
        headers=worker,
    ).json()["id"]
    return {
        "worker": worker,
        "other": auth_header("w2@t.kz"),
        "moderator": auth_header("mod@t.kz"),
        "company_id": company_id,
        "review_id": review_id,
    }


def test_comment_lifecycle(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    base = f"/companies/{ctx['company_id']}/reviews/{ctx['review_id']}/comments"

    # Авторизациясыз жазуға болмайды, оқуға болады
    assert client.post(base, json={"body": "authsyz komment"}).status_code == 401
    assert client.get(base).status_code == 200

    created = client.post(
        base,
        json={"body": "Men de sol zherde istedim, rastaimyn"},
        headers=ctx["other"],
    )
    assert created.status_code == 201
    assert created.json()["author_pseudonym"] == "worker_02"

    # Тым қысқа мәтін
    assert (
        client.post(base, json={"body": "j"}, headers=ctx["other"]).status_code == 422
    )

    comments = client.get(base).json()
    assert len(comments) == 1

    # Модератор жасырса тізімнен шығады, аудит-логқа түседі
    comment_id = comments[0]["id"]
    hide = client.post(
        f"/moderation/comments/{comment_id}/hide",
        json={"reason": "Zheke adam aty atalgan, PII-qorgau"},
        headers=ctx["moderator"],
    )
    assert hide.status_code == 200
    assert client.get(base).json() == []
    log = client.get("/moderation/log").json()
    assert log[0]["target_type"] == "comment"


def test_comment_on_complaint(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    complaint_id = client.post(
        f"/companies/{ctx['company_id']}/complaints",
        json={
            "category": "ghost_vacancy",
            "stage": "call",
            "source_type": "hh",
            "body": REVIEW_BODY,
        },
        headers=ctx["worker"],
    ).json()["id"]
    base = f"/companies/{ctx['company_id']}/complaints/{complaint_id}/comments"
    created = client.post(
        base, json={"body": "Magan da dal osylai istedi olar"}, headers=ctx["other"]
    )
    assert created.status_code == 201
    assert len(client.get(base).json()) == 1
