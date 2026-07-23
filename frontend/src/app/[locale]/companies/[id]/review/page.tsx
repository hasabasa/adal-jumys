"use client";

import { useTranslations } from "next-intl";
import { use, useState } from "react";

import {
  DiscriminationField,
  EMPTY_DISCRIMINATION,
  toApiBlocks,
} from "@/components/forms/discrimination-field";
import { Button } from "@/components/ui/button";
import { useRouter } from "@/i18n/navigation";
import { post } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function ReviewFormPage({
  params,
}: Readonly<{ params: Promise<{ id: string }> }>) {
  const { id } = use(params);
  const t = useTranslations("reviewForm");
  const router = useRouter();
  const [score, setScore] = useState(5);
  const [body, setBody] = useState("");
  const [illegalFines, setIllegalFines] = useState(false);
  const [discrimination, setDiscrimination] = useState(EMPTY_DISCRIMINATION);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await post(
        `/companies/${id}/reviews`,
        {
          overall_score: score,
          body,
          illegal_fines: illegalFines,
          discrimination: toApiBlocks(discrimination),
        },
        getToken(),
      );
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

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={illegalFines}
            onChange={(event) => setIllegalFines(event.target.checked)}
          />
          {t("finesLabel")}
        </label>

        <DiscriminationField
          value={discrimination}
          onChange={setDiscrimination}
        />

        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" disabled={busy}>
          {busy ? "..." : t("submit")}
        </Button>
      </form>
    </div>
  );
}
