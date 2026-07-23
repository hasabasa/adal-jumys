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

const CATEGORIES = [
  "salary_fraud",
  "fake_vacancy",
  "paid_training",
  "unethical_questions",
  "rudeness",
  "ghost_vacancy",
  "unpaid_test_task",
  "discrimination",
];
const STAGES = ["announcement", "call", "interview", "offer"];
const SOURCES = ["hh", "olx", "instagram", "threads", "telegram", "whatsapp", "other"];

export default function ComplaintFormPage({
  params,
}: Readonly<{ params: Promise<{ id: string }> }>) {
  const { id } = use(params);
  const t = useTranslations("complaintForm");
  const tFeed = useTranslations("feed");
  const tCompany = useTranslations("company");
  const router = useRouter();
  const [category, setCategory] = useState("salary_fraud");
  const [stage, setStage] = useState("interview");
  const [sourceType, setSourceType] = useState("hh");
  const [advertised, setAdvertised] = useState("");
  const [actual, setActual] = useState("");
  const [body, setBody] = useState("");
  const [discrimination, setDiscrimination] = useState(EMPTY_DISCRIMINATION);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const isSalaryFraud = category === "salary_fraud";
  const isDiscrimination = category === "discrimination";

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // Бриф-талап: шағымға скрин-дәлел МІНДЕТТІ (вакансиялар өшіріледі)
    if (files.length === 0) {
      setError(t("evidenceRequired"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const complaint = await post<{ id: string }>(
        `/companies/${id}/complaints`,
        {
          category,
          stage,
          source_type: sourceType,
          advertised_salary: isSalaryFraud ? Number(advertised) : null,
          actual_salary: isSalaryFraud ? Number(actual) : null,
          body,
          discrimination: toApiBlocks(discrimination, isDiscrimination),
        },
        getToken(),
      );
      for (const file of files) {
        await uploadFile(
          `/companies/${id}/complaints/${complaint.id}/evidence`,
          file,
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

  const selectClass =
    "h-10 rounded-lg border border-input bg-card px-2 text-sm";

  return (
    <div className="mx-auto max-w-lg px-4 py-12">
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{t("hint")}</p>

      <form onSubmit={onSubmit} className="mt-6 grid gap-4">
        <label className="grid gap-1 text-sm font-medium">
          {t("categoryLabel")}
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className={selectClass}
          >
            {CATEGORIES.map((value) => (
              <option key={value} value={value}>
                {tFeed(`categories.${value}`)}
              </option>
            ))}
          </select>
        </label>

        <div className="grid grid-cols-2 gap-2">
          <label className="grid gap-1 text-sm font-medium">
            {t("stageLabel")}
            <select
              value={stage}
              onChange={(event) => setStage(event.target.value)}
              className={selectClass}
            >
              {STAGES.map((value) => (
                <option key={value} value={value}>
                  {tCompany(`stages.${value}`)}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            {t("sourceLabel")}
            <select
              value={sourceType}
              onChange={(event) => setSourceType(event.target.value)}
              className={selectClass}
            >
              {SOURCES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </div>

        {isSalaryFraud && (
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              min={0}
              required
              value={advertised}
              onChange={(event) => setAdvertised(event.target.value)}
              placeholder={t("advertisedPlaceholder")}
              className="h-10 rounded-lg border border-input bg-card px-3 text-sm"
            />
            <input
              type="number"
              min={0}
              required
              value={actual}
              onChange={(event) => setActual(event.target.value)}
              placeholder={t("actualPlaceholder")}
              className="h-10 rounded-lg border border-input bg-card px-3 text-sm"
            />
          </div>
        )}

        <textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          required
          minLength={50}
          maxLength={10000}
          rows={5}
          placeholder={t("bodyPlaceholder")}
          className="rounded-lg border border-input bg-card px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />

        <DiscriminationField
          value={discrimination}
          onChange={setDiscrimination}
          required={isDiscrimination}
        />

        <div className="rounded-lg border border-border p-3">
          <label className="text-sm font-medium">
            {t("evidenceLabel")} <span className="text-destructive">*</span>
          </label>
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

        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" disabled={busy}>
          {busy ? "..." : t("submit")}
        </Button>
      </form>
    </div>
  );
}
