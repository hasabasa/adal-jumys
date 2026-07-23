"use client";

import { Flag, MoreHorizontal, X } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { FilePicker } from "@/components/forms/file-picker";
import { Button } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { post, uploadFile } from "@/lib/api";
import { getToken } from "@/lib/auth";

const COMPANY_REASONS = [
  "false_facts",
  "defamation",
  "pii_exposed",
  "fake_evidence",
  "other",
];
const USER_REASONS = ["pii_exposed", "insult", "spam", "defamation", "other"];
const ACCEPT = "image/jpeg,image/png,image/webp,application/pdf";

export function PostMenu({
  targetKind,
  targetId,
}: Readonly<{
  targetKind: "reviews" | "complaints" | "comments";
  targetId: string;
}>) {
  const t = useTranslations("report");
  const [menuOpen, setMenuOpen] = useState(false);
  const [step, setStep] = useState<"closed" | "choose" | "form" | "done">(
    "closed",
  );
  const [isCompany, setIsCompany] = useState(false);
  const [reason, setReason] = useState("");
  const [body, setBody] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const authed = getToken() !== null;
  const reasons = isCompany ? COMPANY_REASONS : USER_REASONS;

  function startTrack(company: boolean) {
    setIsCompany(company);
    setReason(company ? "false_facts" : "pii_exposed");
    setStep("form");
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const report = await post<{ id: string }>(
        "/reports",
        {
          target_kind: targetKind,
          target_id: targetId,
          is_company_claim: isCompany,
          reason,
          body: body || null,
        },
        getToken(),
      );
      for (const file of files.slice(0, 3)) {
        await uploadFile(`/reports/${report.id}/evidence`, file, getToken());
      }
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("genericError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label={t("menuLabel")}
        className="rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-accent/50 hover:text-foreground"
      >
        <MoreHorizontal className="size-[18px]" strokeWidth={1.8} />
      </button>

      {menuOpen && (
        <div className="absolute right-0 z-20 mt-1 w-44 rounded-lg border border-border bg-popover p-1 shadow-md">
          <button
            type="button"
            onClick={() => {
              setMenuOpen(false);
              setStep("choose");
            }}
            className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm hover:bg-accent/50"
          >
            <Flag className="size-4" strokeWidth={1.8} />
            {t("reportAction")}
          </button>
        </div>
      )}

      {step !== "closed" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/30 p-4">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-5 shadow-lg">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">{t("title")}</h2>
              <button
                type="button"
                onClick={() => setStep("closed")}
                aria-label={t("close")}
                className="rounded-full p-1 text-muted-foreground hover:text-foreground"
              >
                <X className="size-4" />
              </button>
            </div>

            {!authed ? (
              <p className="mt-4 text-sm text-muted-foreground">
                <Link href="/login" className="text-primary hover:underline">
                  {t("loginPrompt")}
                </Link>
              </p>
            ) : step === "choose" ? (
              <div className="mt-4 grid gap-2">
                <button
                  type="button"
                  onClick={() => startTrack(true)}
                  className="rounded-lg border-2 border-border p-3 text-left transition-colors hover:border-primary"
                >
                  <p className="text-sm font-semibold">{t("companyTrack")}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {t("companyTrackHint")}
                  </p>
                </button>
                <button
                  type="button"
                  onClick={() => startTrack(false)}
                  className="rounded-lg border-2 border-border p-3 text-left transition-colors hover:border-primary"
                >
                  <p className="text-sm font-semibold">{t("userTrack")}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {t("userTrackHint")}
                  </p>
                </button>
              </div>
            ) : step === "form" ? (
              <form onSubmit={onSubmit} className="mt-4 grid gap-3">
                <select
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                  className="h-10 rounded-lg border border-input bg-card px-2 text-sm"
                >
                  {reasons.map((value) => (
                    <option key={value} value={value}>
                      {t(`reasons.${value}`)}
                    </option>
                  ))}
                </select>
                <textarea
                  value={body}
                  onChange={(event) => setBody(event.target.value)}
                  required={isCompany}
                  minLength={isCompany ? 20 : undefined}
                  maxLength={3000}
                  rows={4}
                  placeholder={
                    isCompany
                      ? t("bodyPlaceholderCompany")
                      : t("bodyPlaceholderUser")
                  }
                  className="rounded-lg border border-input bg-card px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                />
                {isCompany && (
                  <div>
                    <p className="mb-1 text-xs font-medium">
                      {t("evidenceLabel")}
                    </p>
                    <FilePicker
                      files={files}
                      onChange={setFiles}
                      multiple
                      maxFiles={3}
                      accept={ACCEPT}
                    />
                    <p className="mt-1 text-xs text-muted-foreground">
                      {t("evidenceHint")}
                    </p>
                  </div>
                )}
                {error && <p className="text-sm text-destructive">{error}</p>}
                <Button type="submit" disabled={busy}>
                  {busy ? "..." : t("submit")}
                </Button>
              </form>
            ) : (
              <div className="mt-4">
                <p className="text-sm">{t("done")}</p>
                <Button
                  className="mt-3"
                  size="sm"
                  onClick={() => setStep("closed")}
                >
                  {t("close")}
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
