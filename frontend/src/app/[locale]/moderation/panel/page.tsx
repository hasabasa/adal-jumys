"use client";

import { useTranslations } from "next-intl";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  authedGet,
  moderationFileUrl,
  post,
  type EvidenceQueueItem,
  type ReportQueueItem,
  type RepresentativeQueueItem,
  type VerificationQueueItem,
} from "@/lib/api";
import { fetchCurrentUser, getToken, type CurrentUser } from "@/lib/auth";

const VERIFICATION_METHODS = ["employment_contract", "bank_statement", "other"];

function ReasonActions({
  onDecision,
  busy,
  approveLabel,
  rejectLabel,
  reasonPlaceholder,
  extra,
}: Readonly<{
  onDecision: (decision: string, reason: string) => void;
  busy: boolean;
  approveLabel: string;
  rejectLabel: string;
  reasonPlaceholder: string;
  extra?: React.ReactNode;
}>) {
  const [reason, setReason] = useState("");
  const valid = reason.trim().length >= 10;
  return (
    <div className="mt-2 flex flex-wrap items-center gap-2">
      <input
        value={reason}
        onChange={(event) => setReason(event.target.value)}
        placeholder={reasonPlaceholder}
        className="h-9 min-w-56 flex-1 rounded-lg border border-input bg-card px-3 text-xs"
      />
      {extra}
      <Button
        size="sm"
        disabled={!valid || busy}
        onClick={() => onDecision("approve", reason)}
      >
        {approveLabel}
      </Button>
      <Button
        size="sm"
        variant="outline"
        disabled={!valid || busy}
        onClick={() => onDecision("reject", reason)}
      >
        {rejectLabel}
      </Button>
    </div>
  );
}

export default function ModerationPanelPage() {
  const t = useTranslations("moderation");
  const [user, setUser] = useState<CurrentUser | null | "loading">("loading");
  const [representatives, setRepresentatives] = useState<
    RepresentativeQueueItem[]
  >([]);
  const [evidence, setEvidence] = useState<EvidenceQueueItem[]>([]);
  const [verifications, setVerifications] = useState<VerificationQueueItem[]>(
    [],
  );
  const [reports, setReports] = useState<ReportQueueItem[]>([]);
  const [method, setMethod] = useState("employment_contract");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const token = getToken();
    const [reps, evid, verif, reps2] = await Promise.all([
      authedGet<RepresentativeQueueItem[]>(
        "/moderation/representatives",
        token,
        [],
      ),
      authedGet<EvidenceQueueItem[]>("/moderation/evidence", token, []),
      authedGet<VerificationQueueItem[]>("/moderation/verifications", token, []),
      authedGet<ReportQueueItem[]>("/moderation/reports", token, []),
    ]);
    setRepresentatives(reps);
    setEvidence(evid);
    setVerifications(verif);
    setReports(reps2);
  }, []);

  useEffect(() => {
    fetchCurrentUser().then((current) => {
      setUser(current);
      if (
        current !== null &&
        (current.trust_level === "moderator" || current.trust_level === "admin")
      ) {
        reload();
      }
    });
  }, [reload]);

  async function decide(path: string, body: unknown) {
    setBusy(true);
    setError(null);
    try {
      await post(path, body, getToken());
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Қате");
    } finally {
      setBusy(false);
    }
  }

  if (user === "loading") {
    return <div className="px-4 py-16 text-center text-sm">...</div>;
  }
  if (
    user === null ||
    (user.trust_level !== "moderator" && user.trust_level !== "admin")
  ) {
    return (
      <div className="px-4 py-16 text-center text-sm text-muted-foreground">
        {t("noAccess")}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="text-2xl font-bold">{t("panelTitle")}</h1>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}

      <section className="mt-8">
        <h2 className="text-sm font-semibold">
          {t("reportsTitle")} ({reports.length})
        </h2>
        {reports.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">{t("queueEmpty")}</p>
        ) : (
          reports.map((item) => (
            <div
              key={item.id}
              className="mt-2 rounded-lg border border-border bg-card p-3 text-sm"
            >
              <div className="flex flex-wrap items-center gap-2 text-xs">
                {item.is_company_claim && (
                  <span className="rounded-md bg-warning/15 px-2 py-0.5 font-medium text-warning">
                    {t("companyClaim")}
                  </span>
                )}
                {item.verified_claim && (
                  <span className="rounded-md bg-success/10 px-2 py-0.5 font-medium text-success">
                    {t("verifiedClaim")}
                  </span>
                )}
                <span className="rounded-md bg-secondary px-2 py-0.5">
                  {t(`reportReasons.${item.reason}`)}
                </span>
                <span className="text-muted-foreground">
                  {item.reporter_pseudonym}
                </span>
              </div>
              {item.body && <p className="mt-1.5">{item.body}</p>}
              {item.evidence_ids.length > 0 && (
                <p className="mt-1.5 text-xs">
                  {item.evidence_ids.map((evidenceId, index) => (
                    <a
                      key={evidenceId}
                      href={moderationFileUrl(evidenceId)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mr-2 text-primary hover:underline"
                    >
                      {t("counterEvidence")} {index + 1}
                    </a>
                  ))}
                </p>
              )}
              <ReasonActions
                busy={busy}
                approveLabel={t("hidePost")}
                rejectLabel={t("keepPost")}
                reasonPlaceholder={t("reasonPlaceholder")}
                onDecision={(decision, reason) =>
                  decide(
                    `/moderation/reports/${item.id}/resolve/${
                      decision === "approve" ? "hide" : "keep"
                    }`,
                    { reason },
                  )
                }
              />
            </div>
          ))
        )}
      </section>

      <section className="mt-8">
        <h2 className="text-sm font-semibold">
          {t("repsTitle")} ({representatives.length})
        </h2>
        {representatives.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">{t("queueEmpty")}</p>
        ) : (
          representatives.map((item) => (
            <div
              key={item.id}
              className="mt-2 rounded-lg border border-border bg-card p-3 text-sm"
            >
              <p>
                <span className="font-medium">{item.user_pseudonym}</span> →{" "}
                {item.company_name}
                <span className="ml-2 text-xs text-muted-foreground">
                  {item.proof_method}
                </span>
              </p>
              <ReasonActions
                busy={busy}
                approveLabel={t("approve")}
                rejectLabel={t("reject")}
                reasonPlaceholder={t("reasonPlaceholder")}
                onDecision={(decision, reason) =>
                  decide(`/moderation/representatives/${item.id}/${decision}`, {
                    reason,
                  })
                }
              />
            </div>
          ))
        )}
      </section>

      <section className="mt-8">
        <h2 className="text-sm font-semibold">
          {t("evidenceTitle")} ({evidence.length})
        </h2>
        {evidence.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">{t("queueEmpty")}</p>
        ) : (
          evidence
            .filter((item) => item.purpose === "public_evidence")
            .map((item) => (
              <div
                key={item.id}
                className="mt-2 rounded-lg border border-border bg-card p-3 text-sm"
              >
                <p className="text-xs text-muted-foreground">
                  {item.mime_type} ·{" "}
                  {Math.round((item.size_bytes ?? 0) / 1024)} KB ·{" "}
                  <a
                    href={moderationFileUrl(item.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    {t("preview")}
                  </a>
                </p>
                <ReasonActions
                  busy={busy}
                  approveLabel={t("approve")}
                  rejectLabel={t("reject")}
                  reasonPlaceholder={t("reasonPlaceholder")}
                  onDecision={(decision, reason) =>
                    decide(`/moderation/evidence/${item.id}/${decision}`, {
                      reason,
                      pii_masked: false,
                    })
                  }
                />
              </div>
            ))
        )}
      </section>

      <section className="mt-8 pb-16">
        <h2 className="text-sm font-semibold">
          {t("verificationsTitle")} ({verifications.length})
        </h2>
        {verifications.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">{t("queueEmpty")}</p>
        ) : (
          verifications.map((item) => (
            <div
              key={item.evidence_id}
              className="mt-2 rounded-lg border border-border bg-card p-3 text-sm"
            >
              <p>
                <span className="font-medium">{item.author_pseudonym}</span> →{" "}
                {item.company_name}{" "}
                <a
                  href={moderationFileUrl(item.evidence_id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline"
                >
                  {t("preview")}
                </a>
              </p>
              <ReasonActions
                busy={busy}
                approveLabel={t("approve")}
                rejectLabel={t("reject")}
                reasonPlaceholder={t("reasonPlaceholder")}
                extra={
                  <select
                    value={method}
                    onChange={(event) => setMethod(event.target.value)}
                    className="h-9 rounded-lg border border-input bg-card px-2 text-xs"
                  >
                    {VERIFICATION_METHODS.map((value) => (
                      <option key={value} value={value}>
                        {t(`methods.${value}`)}
                      </option>
                    ))}
                  </select>
                }
                onDecision={(decision, reason) =>
                  decide(
                    `/moderation/verifications/${item.review_id}/${decision}`,
                    { reason, method },
                  )
                }
              />
            </div>
          ))
        )}
      </section>
    </div>
  );
}
