from tests.conftest import REVIEW_BODY, make_bin

PNG_BYTES = b"\x89PNG\r\n\x1a\nkeri-dalel"


def _setup(client, register, auth_header, promote) -> dict:
    register("w@t.kz", "worker_01")
    register("hr@t.kz", "hr_official", role="company")
    register("mod@t.kz", "mod_bek")
    promote("mod@t.kz", "moderator")
    worker = auth_header("w@t.kz")
    company_id = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Report Test LLP"},
        headers=worker,
    ).json()["id"]
    review_id = client.post(
        f"/companies/{company_id}/reviews",
        json={"overall_score": 2, "body": REVIEW_BODY},
        headers=worker,
    ).json()["id"]
    return {
        "worker": worker,
        "hr": auth_header("hr@t.kz"),
        "moderator": auth_header("mod@t.kz"),
        "company_id": company_id,
        "review_id": review_id,
    }


def test_company_claim_with_counter_evidence(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)

    # Компания-дауға түсіндірме міндетті
    invalid = client.post(
        "/reports",
        json={
            "target_kind": "reviews",
            "target_id": ctx["review_id"],
            "is_company_claim": True,
            "reason": "false_facts",
        },
        headers=ctx["hr"],
    )
    assert invalid.status_code == 422

    created = client.post(
        "/reports",
        json={
            "target_kind": "reviews",
            "target_id": ctx["review_id"],
            "is_company_claim": True,
            "reason": "false_facts",
            "body": "Zhalaqy tolyq tolengen, keri dalel retinde vedomost tirkelefi",
        },
        headers=ctx["hr"],
    )
    assert created.status_code == 201
    report = created.json()
    assert report["verified_claim"] is False  # өкілдігі расталмаған

    # Кері дәлел тіркеу - жарияда ЕШҚАШАН көрінбейді
    upload = client.post(
        f"/reports/{report['id']}/evidence",
        files={"file": ("vedomost.png", PNG_BYTES, "image/png")},
        headers=ctx["hr"],
    )
    assert upload.status_code == 201
    assert client.get(f"/evidence/{upload.json()['id']}").status_code == 404

    # Модератор-кезекте дәлелімен тұр
    queue = client.get("/moderation/reports", headers=ctx["moderator"]).json()
    assert len(queue) == 1
    assert queue[0]["is_company_claim"] is True
    assert len(queue[0]["evidence_ids"]) == 1

    # Шешім: постты жасыру
    resolve = client.post(
        f"/moderation/reports/{report['id']}/resolve/hide",
        json={"reason": "Keri dalel senimdi, post zhasyryldy"},
        headers=ctx["moderator"],
    )
    assert resolve.status_code == 200
    assert client.get(f"/companies/{ctx['company_id']}/reviews").json() == []
    assert client.get("/moderation/reports", headers=ctx["moderator"]).json() == []


def test_user_report_and_keep(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    register("u@t.kz", "user_zhai")

    created = client.post(
        "/reports",
        json={
            "target_kind": "reviews",
            "target_id": ctx["review_id"],
            "reason": "pii_exposed",
            "body": "Skrinde adam nomeri ashyq korinip tur",
        },
        headers=auth_header("u@t.kz"),
    )
    assert created.status_code == 201

    # Компания-трек себебі жай юзерге жүрмейді
    wrong = client.post(
        "/reports",
        json={
            "target_kind": "reviews",
            "target_id": ctx["review_id"],
            "reason": "false_facts",
        },
        headers=auth_header("u@t.kz"),
    )
    assert wrong.status_code == 422

    # Шешім: пост орнында қалады
    resolve = client.post(
        f"/moderation/reports/{created.json()['id']}/resolve/keep",
        json={"reason": "Skrinde PII zhoq, post zaңdy"},
        headers=ctx["moderator"],
    )
    assert resolve.status_code == 200
    assert len(client.get(f"/companies/{ctx['company_id']}/reviews").json()) == 1
