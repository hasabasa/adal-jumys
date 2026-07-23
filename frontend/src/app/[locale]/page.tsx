import { getTranslations, setRequestLocale } from "next-intl/server";

import { FeedList } from "@/components/feed/feed-list";
import { StatCounter } from "@/components/feed/stat-counter";
import { Button } from "@/components/ui/button";
import { getFeed, getStats } from "@/lib/api";

export default async function HomePage({
  params,
}: Readonly<{ params: Promise<{ locale: string }> }>) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("hero");
  const tFeed = await getTranslations("feed");
  const [feedItems, stats] = await Promise.all([getFeed(), getStats()]);

  const statEntries = [
    { value: stats.companies, key: "statsCompanies" },
    { value: stats.reviews, key: "statsReviews" },
    { value: stats.complaints, key: "statsComplaints" },
  ] as const;

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
          {statEntries.map((stat) => (
            <div key={stat.key} className="text-center">
              <dt className="text-2xl font-bold text-primary">
                <StatCounter value={stat.value} />
              </dt>
              <dd className="text-xs text-muted-foreground">{t(stat.key)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="pb-20">
        <h2 className="mb-4 text-lg font-semibold">{tFeed("title")}</h2>
        <FeedList initialItems={feedItems} />
      </section>
    </div>
  );
}
