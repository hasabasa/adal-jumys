from tests.conftest import REVIEW_BODY, make_bin

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-image-data"


def _setup(client, register, auth_header, promote) -> dict:
    register("w@t.kz", "worker_01")
    register("w2@t.kz", "worker_02")
    register("mod@t.kz", "mod_bek")
    promote("mod@t.kz", "moderator")
    worker = auth_header("w@t.kz")
    company_id = client.post(
        "/companies",
        json={"bin": make_bin("12345678901"), "name": "Dalel Test LLP"},
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


def _upload(client, ctx, headers, filename="skrin.png", mime="image/png", data=PNG_BYTES):
    return client.post(
        f"/companies/{ctx['company_id']}/reviews/{ctx['review_id']}/evidence",
        files={"file": (filename, data, mime)},
        headers=headers,
    )


def test_author_uploads_evidence(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    response = _upload(client, ctx, ctx["worker"])
    assert response.status_code == 201
    assert response.json()["mime_type"] == "image/png"


def test_only_author_can_upload(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    assert _upload(client, ctx, ctx["other"]).status_code == 403


def test_disallowed_mime_rejected(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    response = _upload(
        client, ctx, ctx["worker"], filename="virus.exe", mime="application/x-msdownload"
    )
    assert response.status_code == 415


def test_oversized_file_rejected(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    big = b"x" * (11 * 1024 * 1024)
    response = _upload(client, ctx, ctx["worker"], data=big)
    assert response.status_code == 413


def test_moderation_gate(client, register, auth_header, promote):
    """Дәлел модерацияға дейін жарияда КӨРІНБЕЙДІ, approve-тан кейін көрінеді."""
    ctx = _setup(client, register, auth_header, promote)
    evidence_id = _upload(client, ctx, ctx["worker"]).json()["id"]

    listed = client.get(f"/companies/{ctx['company_id']}/reviews").json()
    assert listed[0]["evidence"] == []
    assert client.get(f"/evidence/{evidence_id}").status_code == 404

    queue = client.get("/moderation/evidence", headers=ctx["moderator"]).json()
    assert len(queue) == 1

    preview = client.get(
        f"/moderation/evidence/{evidence_id}/file", headers=ctx["moderator"]
    )
    assert preview.status_code == 200

    approve = client.post(
        f"/moderation/evidence/{evidence_id}/approve",
        json={"reason": "Skrin zharamdy, PII zhoq", "pii_masked": False},
        headers=ctx["moderator"],
    )
    assert approve.status_code == 200

    listed = client.get(f"/companies/{ctx['company_id']}/reviews").json()
    assert listed[0]["evidence"][0]["id"] == evidence_id
    served = client.get(f"/evidence/{evidence_id}")
    assert served.status_code == 200
    assert served.content == PNG_BYTES


def test_reject_keeps_file_hidden(client, register, auth_header, promote):
    ctx = _setup(client, register, auth_header, promote)
    evidence_id = _upload(client, ctx, ctx["worker"]).json()["id"]
    reject = client.post(
        f"/moderation/evidence/{evidence_id}/reject",
        json={"reason": "PII ashyq korinip tur, maskasyz zhariyalanbaidy"},
        headers=ctx["moderator"],
    )
    assert reject.status_code == 200
    assert client.get(f"/evidence/{evidence_id}").status_code == 404
    assert client.get(f"/companies/{ctx['company_id']}/reviews").json()[0]["evidence"] == []
