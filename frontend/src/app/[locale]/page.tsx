import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { use } from "react";

import { Button } from "@/components/ui/button";

// TODO: сандар мен лента backend API-ге қосылады (GET /feed - келесі қадам)
const PLACEHOLDER_STATS = [
  { value: "—", key: "statsCompanies" },
  { value: "—", key: "statsReviews" },
  { value: "—", key: "statsComplaints" },
] as const;

export default function HomePage({
  params,
}: Readonly<{ params: Promise<{ locale: string }> }>) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations("hero");
  const tFeed = useTranslations("feed");

  return (
    <div className="mx-auto max-w-6xl px-4">
      <section className="flex flex-col items-center py-20 text-center sm:py-28">
        <h1 className="max-w-2xl text-4xl font-bold tracking-tight text-balance sm:text-5xl">
          {t("title")}
        </h1>
        <p className="mt-4 max-w-xl text-muted-foreground text-balance">
          {t("subtitle")}
        </p>

        <form
          action="/companies"
          className="mt-8 flex w-full max-w-xl items-center gap-2"
        >
          <input
            type="search"
            name="search"
            placeholder={t("searchPlaceholder")}
            className="h-11 flex-1 rounded-lg border border-input bg-card px-4 text-sm outline-none transition-shadow focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          />
          <Button type="submit" size="lg" className="h-11">
            {t("searchButton")}
          </Button>
        </form>

        <dl className="mt-10 flex gap-10">
          {PLACEHOLDER_STATS.map((stat) => (
            <div key={stat.key} className="text-center">
              <dt className="text-2xl font-bold text-primary">{stat.value}</dt>
              <dd className="text-xs text-muted-foreground">{t(stat.key)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="pb-20">
        <h2 className="mb-4 text-lg font-semibold">{tFeed("title")}</h2>
        <div className="grid gap-3">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="flex h-24 items-center justify-center rounded-xl border border-dashed border-border text-sm text-muted-foreground"
            >
              {i === 1 ? tFeed("comingSoon") : ""}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
