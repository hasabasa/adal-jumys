"use client";

import { useTranslations } from "next-intl";
import { use, useState } from "react";

import {
  DiscriminationField,
  EMPTY_DISCRIMINATION,
  toApiBlocks,
} from "@/components/forms/discrimination-field";
import { FilePicker } from "@/components/forms/file-picker";
import { Button } from "@/components/ui/button";
import { useRouter } from "@/i18n/navigation";
import { post, uploadFile } from "@/lib/api";
import { getToken } from "@/lib/auth";

const ACCEPT =
  "image/jpeg,image/png,image/webp,application/pdf,audio/mpeg,audio/ogg,video/mp4";

const PROBLEMS = [
  "unpaid_salary",
  "delayed_salary",
  "no_pension_contributions",
  "unpaid_overtime",
  "unpaid_holiday_work",
  "no_contract",
  "illegal_fines",
  "no_vacation",
  "no_sick_leave",
  "unsafe_conditions",
  "illegal_dismissal",
  "no_final_settlement",
  "forced_labor",
];

export default function ReviewFormPage({
  params,
}: Readonly<{ params: Promise<{ id: string }> }>) {
  const { id } = use(params);
  const t = useTranslations("reviewForm");
  const tProblems = useTranslations("problems");
  const router = useRouter();
  const [score, setScore] = useState(5);
  const [body, setBody] = useState("");
  const [problems, setProblems] = useState<string[]>([]);
  const [pros, setPros] = useState("");
  const [cons, setCons] = useState("");
  const [discrimination, setDiscrimination] = useState(EMPTY_DISCRIMINATION);
  const [files, setFiles] = useState<File[]>([]);
  const [verificationFiles, setVerificationFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const review = await post<{ id: string }>(
        `/companies/${id}/reviews`,
        {
          overall_score: score,
          body,
          pros: pros || null,
          cons: cons || null,
          problems,
          discrimination: toApiBlocks(discrimination),
        },
        getToken(),
      );
      for (const file of files) {
        await uploadFile(
          `/companies/${id}/reviews/${review.id}/evidence`,
          file,
          getToken(),
        );
      }
      if (verificationFiles[0]) {
        await uploadFile(
          `/companies/${id}/reviews/${review.id}/verification`,
          verificationFiles[0],
          getToken(),
        );
      }
      router.push(`/companies/${id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("genericError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-12">
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{t("factHint")}</p>

      <form onSubmit={onSubmit} className="mt-6 grid gap-4">
        <div>
          <label className="text-sm font-medium">
            {t("scoreLabel")}: <span className="font-bold">{score}/10</span>
          </label>
          <input
            type="range"
            min={1}
            max={10}
            value={score}
            onChange={(event) => setScore(Number(event.target.value))}
            className="mt-2 w-full accent-[var(--primary)]"
          />
        </div>

        <textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          required
          minLength={50}
          maxLength={10000}
          rows={6}
          placeholder={t("bodyPlaceholder")}
          className="rounded-lg border border-input bg-card px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        <p className="text-xs text-muted-foreground">{t("anonHint")}</p>

        <div className="grid gap-2 sm:grid-cols-2">
          <textarea
            value={pros}
            onChange={(event) => setPros(event.target.value)}
            maxLength={3000}
            rows={3}
            placeholder={t("prosPlaceholder")}
            className="rounded-lg border border-success/40 bg-card px-3 py-2 text-sm outline-none focus-visible:border-success focus-visible:ring-3 focus-visible:ring-success/30"
          />
          <textarea
            value={cons}
            onChange={(event) => setCons(event.target.value)}
            maxLength={3000}
            rows={3}
            placeholder={t("consPlaceholder")}
            className="rounded-lg border border-destructive/40 bg-card px-3 py-2 text-sm outline-none focus-visible:border-destructive focus-visible:ring-3 focus-visible:ring-destructive/30"
          />
        </div>

        <fieldset className="rounded-lg border border-border p-3">
          <legend className="px-1 text-sm font-medium">
            {t("problemsLabel")}
          </legend>
          <div className="grid gap-1.5">
            {PROBLEMS.map((problem) => (
              <label key={problem} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={problems.includes(problem)}
                  onChange={(event) =>
                    setProblems((current) =>
                      event.target.checked
                        ? [...current, problem]
                        : current.filter((value) => value !== problem),
                    )
                  }
                />
                {tProblems(problem)}
              </label>
            ))}
          </div>
        </fieldset>

        <DiscriminationField
          value={discrimination}
          onChange={setDiscrimination}
        />

        <div className="rounded-lg border border-border p-3">
          <label className="text-sm font-medium">{t("evidenceLabel")}</label>
          <div className="mt-2">
            <FilePicker
              files={files}
              onChange={setFiles}
              multiple
              accept={ACCEPT}
            />
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {t("evidenceHint")}
          </p>
        </div>

        <div className="rounded-lg border border-border p-3">
          <label className="text-sm font-medium">{t("verificationLabel")}</label>
          <div className="mt-2">
            <FilePicker
              files={verificationFiles}
              onChange={setVerificationFiles}
              accept={ACCEPT}
            />
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {t("verificationHint")}
          </p>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" disabled={busy}>
          {busy ? "..." : t("submit")}
        </Button>
      </form>
    </div>
  );
}
