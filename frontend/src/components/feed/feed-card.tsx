import { useLocale, useTranslations } from "next-intl";

import { Avatar } from "@/components/feed/avatar";
import { ShareButton } from "@/components/feed/share-button";
import { Link } from "@/i18n/navigation";
import type { FeedItem } from "@/lib/api";
import { formatTenge, relativeTime } from "@/lib/format";
import { cn } from "@/lib/utils";

export function FeedCard({ item }: Readonly<{ item: FeedItem }>) {
  const t = useTranslations("feed");
  const locale = useLocale();
  const isComplaint = item.type === "complaint";

  return (
    <article className="rounded-xl border border-border bg-card p-4 transition-colors hover:border-ring/40">
      <Link href={`/companies/${item.company_id}`} className="block">
        <div className="flex items-center gap-2.5">
          <Avatar name={item.author_pseudonym} />
          <div className="min-w-0">
            <p className="text-sm font-semibold">
              {item.author_pseudonym}
              <span className="ml-2 font-normal text-muted-foreground">
                {relativeTime(item.created_at, locale)}
              </span>
            </p>
            <p className="truncate text-xs text-muted-foreground">
              {item.company_name}
            </p>
          </div>
        </div>

        <p className="mt-2.5 line-clamp-3 text-sm">{item.body}</p>

        {item.salary_diff_percent !== null &&
          item.advertised_salary !== null &&
          item.actual_salary !== null && (
            <p className="mt-2 text-sm">
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

        <div className="mt-2.5 flex flex-wrap items-center gap-2 text-xs">
          <span
            className={cn(
              "rounded-md px-2 py-0.5 font-medium",
              isComplaint
                ? "bg-destructive/10 text-destructive"
                : "bg-accent text-accent-foreground",
            )}
          >
            {isComplaint ? t(`categories.${item.category}`) : t("reviewLabel")}
          </span>
          {item.verification_status === "verified" && (
            <span className="rounded-md bg-success/10 px-2 py-0.5 font-medium text-success">
              {t("verified")}
            </span>
          )}
          {item.overall_score !== null && (
            <span className="font-semibold">{item.overall_score}/10</span>
          )}
        </div>
      </Link>

      <div className="mt-3 flex items-center gap-4 border-t border-border pt-2.5">
        <ShareButton companyId={item.company_id} />
      </div>
    </article>
  );
}
