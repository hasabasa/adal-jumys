"use client";

import { BadgeCheck } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { authedGet, post } from "@/lib/api";
import { fetchCurrentUser, getToken } from "@/lib/auth";

// Бір беттегі компоненттер өкілдік-статусты бөліседі
const statusCache = new Map<string, Promise<string>>();

export function representationStatus(companyId: string): Promise<string> {
  if (!statusCache.has(companyId)) {
    statusCache.set(
      companyId,
      authedGet<{ status: string }>(
        `/companies/${companyId}/representatives/me`,
        getToken(),
        { status: "none" },
      ).then((data) => data.status),
    );
  }
  return statusCache.get(companyId)!;
}

const PROOF_METHODS = ["domain_email", "official_letter", "other"];

export function RepresentButton({
  companyId,
}: Readonly<{ companyId: string }>) {
  const t = useTranslations("represent");
  const [visible, setVisible] = useState(false);
  const [repStatus, setRepStatus] = useState("none");
  const [open, setOpen] = useState(false);
  const [proof, setProof] = useState("domain_email");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCurrentUser().then((user) => {
      if (user?.role !== "company") return;
      setVisible(true);
      representationStatus(companyId).then(setRepStatus);
    });
  }, [companyId]);

  if (!visible) return null;

  if (repStatus === "approved") {
    return (
      <span className="flex items-center gap-1 rounded-md bg-success/10 px-2 py-1 text-xs font-medium text-success">
        <BadgeCheck className="size-3.5" /> {t("approved")}
      </span>
    );
  }
  if (repStatus === "pending") {
    return (
      <span className="rounded-md bg-secondary px-2 py-1 text-xs text-muted-foreground">
        {t("pending")}
      </span>
    );
  }
  if (repStatus === "rejected") {
    return (
      <span className="rounded-md bg-secondary px-2 py-1 text-xs text-muted-foreground">
        {t("rejected")}
      </span>
    );
  }

  async function onSubmit() {
    setBusy(true);
    setError(null);
    try {
      await post(
        `/companies/${companyId}/representatives`,
        { proof_method: proof },
        getToken(),
      );
      statusCache.delete(companyId);
      setRepStatus("pending");
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("genericError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="rounded-md border border-border px-2 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-primary"
      >
        {t("claimButton")}
      </button>
      {open && (
        <div className="mt-2 rounded-lg border border-border bg-card p-3">
          <p className="text-xs text-muted-foreground">{t("hint")}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <select
              value={proof}
              onChange={(event) => setProof(event.target.value)}
              className="h-9 rounded-lg border border-input bg-card px-2 text-xs"
            >
              {PROOF_METHODS.map((value) => (
                <option key={value} value={value}>
                  {t(`proofs.${value}`)}
                </option>
              ))}
            </select>
            <Button size="sm" onClick={onSubmit} disabled={busy}>
              {busy ? "..." : t("submit")}
            </Button>
          </div>
          {error && <p className="mt-1 text-xs text-destructive">{error}</p>}
        </div>
      )}
    </div>
  );
}
