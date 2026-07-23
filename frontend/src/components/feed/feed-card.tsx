import { useLocale, useTranslations } from "next-intl";

import type { FeedItem } from "@/lib/api";
import { cn } from "@/lib/utils";

function formatTenge(value: number, locale: string): string {
  return new Intl.NumberFormat(locale === "kk" ? "kk-KZ" : "ru-KZ").format(value);
}

function relativeTime(iso: string, locale: string): string {
  const seconds = (new Date(iso).getTime() - Date.now()) / 1000;
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
  const table: [Intl.RelativeTimeFormatUnit, number][] = [
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
  ];
  for (const [unit, size] of table) {
    if (Math.abs(seconds) >= size) {
      return rtf.format(Math.round(seconds / size), unit);
    }
  }
  return rtf.format(Math.round(seconds), "second");
}

export function FeedCard({ item }: Readonly<{ item: FeedItem }>) {
  const t = useTranslations("feed");
  const locale = useLocale();
  const isComplaint = item.type === "complaint";

  return (
    <article className="rounded-xl border border-border bg-card p-4 transition-colors hover:border-ring/40">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span
          className={cn(
            "rounded-md px-2 py-0.5 font-medium",
            isComplaint
              ? "bg-destructive/10 text-destructive"
              : "bg-accent text-accent-foreground",
          )}
        >
          {isComplaint
            ? t(`categories.${item.category}`)
            : t("reviewLabel")}
        </span>
        {item.verification_status === "verified" && (
          <span className="rounded-md bg-success/10 px-2 py-0.5 font-medium text-success">
            {t("verified")}
          </span>
        )}
        {item.overall_score !== null && (
          <span className="font-semibold text-foreground">
            {item.overall_score}/10
          </span>
        )}
        <span className="ml-auto text-muted-foreground">
          {relativeTime(item.created_at, locale)}
        </span>
      </div>

      <h3 className="mt-2 text-sm font-semibold">{item.company_name}</h3>

      {item.salary_diff_percent !== null &&
        item.advertised_salary !== null &&
        item.actual_salary !== null && (
          <p className="mt-1 text-sm">
            <span className="text-muted-foreground line-through">
              {formatTenge(item.advertised_salary, locale)} ₸
            </span>{" "}
            <span aria-hidden>→</span>{" "}
            <span className="font-semibold">
              {formatTenge(item.actual_salary, locale)} ₸
            </span>{" "}
            <span className="font-bold text-destructive">
              ({item.salary_diff_percent}%)
            </span>
          </p>
        )}

      <p className="mt-1.5 line-clamp-2 text-sm text-muted-foreground">
        {item.body}
      </p>

      <p className="mt-2 text-xs text-muted-foreground">
        {item.author_pseudonym}
      </p>
    </article>
  );
}
