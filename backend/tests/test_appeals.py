from tests.conftest import REVIEW_BODY, make_bin


def _setup(client, register, auth_header, promote) -> dict:
    register("w@t.kz", "worker_01")
    register("mod1@t.kz", "mod_birinshi")
    register("mod2@t.kz", "mod_ekinshi")
    promote("mod1@t.kz", "moderator")
    promote("mod2@t.kz", "moderator")
    worker = auth_header("w@t.kz")
    company_id = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Appeal Test LLP"},
        headers=worker,
    ).json()["id"]
    review_id = client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 2, "body": REVIEW_BODY},
        headers=worker,
    ).json()["id"]
    action_id = client.post(
        f"/moderation/reviews/{review_id}/hide",
        json={"reason": "Dalelsiz dep saneldi, zhasyryldy"},
        headers=auth_header("mod1@t.kz"),
    ).json()["id"]
    return {
        "worker": worker,
        "mod1": auth_header("mod1@t.kz"),
        "mod2": auth_header("mod2@t.kz"),
        "action_id": action_id,
    }


def test_appeal_lifecycle(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    appeal = client.post(
        f"/moderation/actions/{ctx['action_id']}/appeal",
        json={"body": "Dalel bar edi, skrin qosa tirkelgen, sheshim qate"},
        headers=ctx["worker"],
    )
    assert appeal.status_code == 201
    appeal_id = appeal.json()["id"]

    duplicate = client.post(
        f"/moderation/actions/{ctx['action_id']}/appeal",
        json={"body": "Tagy bir apellyacia beremin dep otyr"},
        headers=ctx["worker"],
    )
    assert duplicate.status_code == 409

    queue = client.get("/moderation/appeals", headers=ctx["mod2"]).json()
    assert len(queue) == 1

    # Екі адам қағидасы: өз шешіміне өзі қарай алмайды
    self_resolve = client.post(
        f"/moderation/appeals/{appeal_id}/uphold",
        json={"reason": "oz sheshimimdi ozim qoldaimyn"},
        headers=ctx["mod1"],
    )
    assert self_resolve.status_code == 403

    overturn = client.post(
        f"/moderation/appeals/{appeal_id}/overturn",
        json={"reason": "Dalel zhetkilikti, zhasyru qate boldy"},
        headers=ctx["mod2"],
    )
    assert overturn.status_code == 200
    assert overturn.json()["action"] == "appeal_overturn"

    resolved_again = client.post(
        f"/moderation/appeals/{appeal_id}/uphold",
        json={"reason": "qaita qarau talaby"},
        headers=ctx["mod2"],
    )
    assert resolved_again.status_code == 409


def test_overturn_stats_public(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    appeal_id = client.post(
        f"/moderation/actions/{ctx['action_id']}/appeal",
        json={"body": "Sheshim qate, dalelim boldy, qaraudy suraimyn"},
        headers=ctx["worker"],
    ).json()["id"]
    client.post(
        f"/moderation/appeals/{appeal_id}/overturn",
        json={"reason": "Apellyacia oryndy, sheshim buzyldy"},
        headers=ctx["mod2"],
    )
    stats = client.get("/moderation/overturn-stats").json()
    by_name = {s["moderator_pseudonym"]: s for s in stats}
    assert by_name["mod_birinshi"]["overturned"] == 1
    assert by_name["mod_birinshi"]["total_actions"] >= 1
