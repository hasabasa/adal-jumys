import { getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import {
  getBadges,
  getCompany,
  getComplaints,
  getComplaintStats,
  getRating,
  getReviews,
} from "@/lib/api";
import { cn } from "@/lib/utils";

export default async function CompanyPage({
  params,
}: Readonly<{ params: Promise<{ locale: string; id: string }> }>) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("company");
  const tFeed = await getTranslations("feed");
  const tDiscr = await getTranslations("discr");

  const company = await getCompany(id);
  if (company === null) notFound();

  const [rating, badges, reviews, complaints, stats] = await Promise.all([
    getRating(id),
    getBadges(id),
    getReviews(id),
    getComplaints(id),
    getComplaintStats(id),
  ]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{company.name}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("bin")}: {company.bin}
            {company.city ? ` · ${company.city}` : ""}
          </p>
          {company.address && (
            <p className="mt-0.5 text-sm text-muted-foreground">
              {company.address}
            </p>
          )}
        </div>
        <div className="text-center">
          <div className="text-4xl font-bold text-primary">
            {rating.rating ?? "—"}
          </div>
          <div className="text-xs text-muted-foreground">
            {t("ratingCaption", {
              count: rating.review_count,
              verified: rating.verified_count,
            })}
          </div>
        </div>
      </div>

      {badges.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {badges.map((badge) => (
            <span
              key={badge.badge}
              title={badge.note ?? undefined}
              className="rounded-md bg-destructive/10 px-2.5 py-1 text-xs font-medium text-destructive"
            >
              {t(`badges.${badge.badge}`)}
            </span>
          ))}
        </div>
      )}

      <div className="mt-6 flex flex-wrap gap-2">
        <Button render={<Link href={`/companies/${id}/review`} />}>
          {t("leaveReview")}
        </Button>
        <Button
          variant="outline"
          render={<Link href={`/companies/${id}/complain`} />}
        >
          {t("leaveComplaint")}
        </Button>
      </div>

      <section className="mt-10">
        <h2 className="text-lg font-semibold">
          {t("reviewsTitle", { count: reviews.length })}
        </h2>
        {reviews.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">{t("noReviews")}</p>
        ) : (
          <div className="mt-4 grid gap-3">
            {reviews.map((review) => (
              <article
                key={review.id}
                className="rounded-xl border border-border bg-card p-4"
              >
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="text-base font-bold">
                    {review.overall_score}/10
                  </span>
                  {review.verification_status === "verified" && (
                    <span className="rounded-md bg-success/10 px-2 py-0.5 font-medium text-success">
                      {tFeed("verified")}
                    </span>
                  )}
                  {review.illegal_fines && (
                    <span className="rounded-md bg-destructive/10 px-2 py-0.5 font-medium text-destructive">
                      {t("illegalFines")}
                    </span>
                  )}
                  {review.discrimination.map((block, index) => (
                    <span
                      key={index}
                      className="rounded-md bg-destructive/10 px-2 py-0.5 font-medium text-destructive"
                    >
                      {tDiscr(`kinds.${block.kind}`)}
                    </span>
                  ))}
                  <span className="ml-auto text-muted-foreground">
                    {review.author_pseudonym}
                  </span>
                </div>
                <p className="mt-2 text-sm">{review.body}</p>
                {review.company_response && (
                  <div className="mt-3 rounded-lg bg-secondary p-3">
                    <p className="text-xs font-semibold">
                      {t("companyResponse")}
                    </p>
                    <p className="mt-1 text-sm">
                      {review.company_response.body}
                    </p>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="mt-10 pb-16">
        <h2 className="text-lg font-semibold">
          {t("complaintsTitle", { count: stats.total })}
        </h2>
        {stats.total > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(stats.by_category).map(([category, count]) => (
              <span
                key={category}
                className="rounded-md bg-secondary px-2.5 py-1 text-xs"
              >
                {tFeed(`categories.${category}`)}: {count}
              </span>
            ))}
          </div>
        )}
        {complaints.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            {t("noComplaints")}
          </p>
        ) : (
          <div className="mt-4 grid gap-3">
            {complaints.map((complaint) => (
              <article
                key={complaint.id}
                className="rounded-xl border border-border bg-card p-4"
              >
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="rounded-md bg-destructive/10 px-2 py-0.5 font-medium text-destructive">
                    {tFeed(`categories.${complaint.category}`)}
                  </span>
                  <span className="text-muted-foreground">
                    {t(`stages.${complaint.stage}`)} ·{" "}
                    {complaint.source_type}
                  </span>
                  <span className="ml-auto text-muted-foreground">
                    {complaint.author_pseudonym}
                  </span>
                </div>
                {complaint.salary_diff_percent !== null && (
                  <p className={cn("mt-2 text-sm font-semibold")}>
                    {complaint.advertised_salary?.toLocaleString("kk-KZ")} ₸ →{" "}
                    {complaint.actual_salary?.toLocaleString("kk-KZ")} ₸{" "}
                    <span className="text-destructive">
                      ({complaint.salary_diff_percent}%)
                    </span>
                  </p>
                )}
                <p className="mt-2 text-sm">{complaint.body}</p>
                {complaint.company_response && (
                  <div className="mt-3 rounded-lg bg-secondary p-3">
                    <p className="text-xs font-semibold">
                      {t("companyResponse")}
                    </p>
                    <p className="mt-1 text-sm">
                      {complaint.company_response.body}
                    </p>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
