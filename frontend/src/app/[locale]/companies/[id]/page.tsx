import { getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";

import { CommentsSection } from "@/components/comments/comments-section";
import { HelpfulButton } from "@/components/feed/helpful-button";
import { Avatar } from "@/components/feed/avatar";
import { ShareButton } from "@/components/feed/share-button";
import { ModeratorTools } from "@/components/moderation/moderator-tools";
import { PostMenu } from "@/components/moderation/post-menu";
import { Button } from "@/components/ui/button";
import { relativeTime } from "@/lib/format";
import { Link } from "@/i18n/navigation";
import {
  evidenceUrl,
  getBadges,
  getCompany,
  getComplaints,
  getComplaintStats,
  getRating,
  getReviews,
  type Evidence,
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
  const tProblems = await getTranslations("problems");

  const company = await getCompany(id);
  if (company === null) notFound();

  function EvidenceLinks({ items }: Readonly<{ items: Evidence[] }>) {
    if (items.length === 0) return null;
    return (
      <div className="mt-2 flex flex-wrap gap-2">
        {items.map((item, index) => (
          <a
            key={item.id}
            href={evidenceUrl(item.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md border border-border px-2 py-0.5 text-xs text-primary transition-colors hover:border-ring/40"
          >
            {t("evidenceItem", { number: index + 1 })}
          </a>
        ))}
      </div>
    );
  }

  const [rating, badges, reviews, complaints, stats] = await Promise.all([
    getRating(id),
    getBadges(id),
    getReviews(id),
    getComplaints(id),
    getComplaintStats(id),
  ]);

  // Бір хронологиялық лента: қызметкер мен кандидат сын-пікірлері аралас
  const posts = [
    ...reviews.map((review) => ({
      kind: "review" as const,
      created_at: review.created_at,
      review,
    })),
    ...complaints.map((complaint) => ({
      kind: "complaint" as const,
      created_at: complaint.created_at,
      complaint,
    })),
  ].sort((a, b) => b.created_at.localeCompare(a.created_at));

  // Glassdoor-үлгі: баға-үлестірім гистограммасы (10-баллдық шкала 5 топқа)
  const bucketLabels = ["9-10", "7-8", "5-6", "3-4", "1-2"];
  const bucketCounts = [0, 0, 0, 0, 0];
  for (const review of reviews) {
    const index = Math.min(4, Math.floor((10 - review.overall_score) / 2));
    bucketCounts[index] += 1;
  }

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
          {company.oked && (
            <p className="mt-0.5 text-sm text-muted-foreground">
              {t("oked")}: {company.oked}
            </p>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            {company.two_gis_url && (
              <a
                href={company.two_gis_url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-md border border-border px-2 py-1 transition-colors hover:border-ring/40 hover:text-primary"
              >
                2GIS
              </a>
            )}
            {company.website && (
              <a
                href={company.website}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-md border border-border px-2 py-1 transition-colors hover:border-ring/40 hover:text-primary"
              >
                {t("website")}
              </a>
            )}
            {company.instagram_url && (
              <a
                href={company.instagram_url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-md border border-border px-2 py-1 transition-colors hover:border-ring/40 hover:text-primary"
              >
                Instagram
              </a>
            )}
            <span className="text-muted-foreground">
              {company.source === "registry_import"
                ? t("sourceRegistry")
                : t("sourceUser")}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <div className="font-display text-2xl font-bold text-primary">
            {rating.rating ?? "—"}
            <span className="text-sm font-normal text-muted-foreground">
              /10
            </span>
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            {t("tiles.rating")}
          </div>
        </div>

        <div
          className={cn(
            "rounded-xl border p-4 text-center",
            badges.length >= 3
              ? "border-destructive/40 bg-destructive/10"
              : badges.length > 0
                ? "border-warning/40 bg-warning/10"
                : "border-border bg-card",
          )}
        >
          <div
            className={cn(
              "font-display text-2xl font-bold",
              badges.length >= 3
                ? "text-destructive"
                : badges.length > 0
                  ? "text-warning"
                  : "text-success",
            )}
          >
            {badges.length}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            {t("tiles.riskFactors")}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <div className="font-display text-2xl font-bold">{rating.review_count}</div>
          <div className="mt-1 text-xs text-muted-foreground">
            {t("tiles.reviews", { verified: rating.verified_count })}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <div className="font-display text-2xl font-bold">{stats.total}</div>
          <div className="mt-1 text-xs text-muted-foreground">
            {t("tiles.complaints")}
          </div>
        </div>
      </div>

      {reviews.length > 0 && (
        <section className="mt-4 rounded-xl border border-border bg-card p-4">
          <h2 className="text-sm font-semibold">{t("distributionTitle")}</h2>
          <div className="mt-3 grid gap-1.5">
            {bucketLabels.map((label, index) => (
              <div key={label} className="flex items-center gap-2 text-xs">
                <span className="w-8 text-right text-muted-foreground">
                  {label}
                </span>
                <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{
                      width: `${(bucketCounts[index] / reviews.length) * 100}%`,
                    }}
                  />
                </div>
                <span className="w-6 text-muted-foreground">
                  {bucketCounts[index]}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {badges.length > 0 && (
        <section className="mt-4 rounded-xl border border-destructive/30 bg-destructive/5 p-4">
          <h2 className="text-sm font-semibold text-destructive">
            {t("riskTitle")}
          </h2>
          <div className="mt-2 flex flex-wrap gap-2">
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
          <p className="mt-2 text-xs text-muted-foreground">{t("riskNote")}</p>
        </section>
      )}

      <section className="mt-4 rounded-xl border border-dashed border-border p-4">
        <h2 className="text-sm font-semibold">{t("officialTitle")}</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          {t("officialSoon")}
        </p>
      </section>

      <div className="mt-6">
        <Button size="lg" render={<Link href={`/companies/${id}/write`} />}>
          {t("writeButton")}
        </Button>
      </div>

      {stats.total > 0 && (
        <section className="mt-6">
          <h2 className="text-sm font-semibold">{t("candidateStatsTitle")}</h2>
          <div className="mt-2 flex flex-wrap gap-2">
            {Object.entries(stats.by_category).map(([category, count]) => (
              <span
                key={category}
                className="rounded-md bg-secondary px-2.5 py-1 text-xs"
              >
                {tFeed(`categories.${category}`)}: {count}
              </span>
            ))}
          </div>
        </section>
      )}

      <section className="mt-10 pb-16">
        <h2 className="text-lg font-semibold">
          {t("postsTitle", { count: reviews.length + complaints.length })}
        </h2>
        {reviews.length + complaints.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">{t("noPosts")}</p>
        ) : (
          <div className="mt-4 grid gap-3">
            {posts.map((post) =>
              post.kind === "review" ? (
                renderReview(post.review)
              ) : (
                renderComplaint(post.complaint)
              ),
            )}
          </div>
        )}
      </section>
    </div>
  );

  function renderReview(review: (typeof reviews)[number]) {
    return (
              <article
                key={review.id}
                className="rounded-xl border border-border bg-card p-4"
              >
                <div className="flex items-center gap-2.5">
                  <Avatar name={review.author_pseudonym} />
                  <p className="min-w-0 text-sm font-semibold">
                    {review.author_pseudonym}
                    <span className="ml-2 font-normal text-muted-foreground">
                      {relativeTime(review.created_at, locale)}
                    </span>
                  </p>
                  <span className="ml-auto text-base font-bold">
                    {review.overall_score}/10
                  </span>
                  <PostMenu targetKind="reviews" targetId={review.id} />
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                  <span className="rounded-md bg-accent px-2 py-0.5 font-medium text-accent-foreground">
                    {t("originWorker")}
                  </span>
                  {review.verification_status === "verified" && (
                    <span className="rounded-md bg-success/10 px-2 py-0.5 font-medium text-success">
                      {tFeed("verified")}
                    </span>
                  )}
                  {review.problems.map((problem) => (
                    <span
                      key={problem}
                      className="rounded-md bg-destructive/10 px-2 py-0.5 font-medium text-destructive"
                    >
                      {tProblems(problem)}
                    </span>
                  ))}
                  {review.discrimination.map((block, index) => (
                    <span
                      key={index}
                      className="rounded-md bg-destructive/10 px-2 py-0.5 font-medium text-destructive"
                    >
                      {tDiscr(`kinds.${block.kind}`)}
                    </span>
                  ))}
                </div>
                <p className="mt-2 text-sm">{review.body}</p>
                {(review.pros || review.cons) && (
                  <div className="mt-2 grid gap-2 sm:grid-cols-2">
                    {review.pros && (
                      <div className="rounded-lg border border-success/30 bg-success/5 p-2.5 text-sm">
                        <p className="text-xs font-semibold text-success">
                          {t("prosTitle")}
                        </p>
                        <p className="mt-0.5">{review.pros}</p>
                      </div>
                    )}
                    {review.cons && (
                      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-2.5 text-sm">
                        <p className="text-xs font-semibold text-destructive">
                          {t("consTitle")}
                        </p>
                        <p className="mt-0.5">{review.cons}</p>
                      </div>
                    )}
                  </div>
                )}
                <EvidenceLinks items={review.evidence} />
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
                <div className="mt-3 flex items-center gap-2 border-t border-border pt-2.5">
                  <HelpfulButton
                    companyId={id}
                    kind="reviews"
                    postId={review.id}
                    initialCount={review.helpful_count}
                  />
                  <CommentsSection
                    companyId={id}
                    kind="reviews"
                    postId={review.id}
                  />
                  <ShareButton companyId={id} />
                </div>
                <ModeratorTools targetKind="reviews" targetId={review.id} />
              </article>
    );
  }

  function renderComplaint(complaint: (typeof complaints)[number]) {
    return (
              <article
                key={complaint.id}
                className="rounded-xl border border-border bg-card p-4"
              >
                <div className="flex items-center gap-2.5">
                  <Avatar name={complaint.author_pseudonym} />
                  <p className="min-w-0 text-sm font-semibold">
                    {complaint.author_pseudonym}
                    <span className="ml-2 font-normal text-muted-foreground">
                      {relativeTime(complaint.created_at, locale)}
                    </span>
                  </p>
                  <span className="ml-auto">
                    <PostMenu targetKind="complaints" targetId={complaint.id} />
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                  <span className="rounded-md bg-secondary px-2 py-0.5 font-medium">
                    {t("originCandidate")}
                  </span>
                  <span className="rounded-md bg-destructive/10 px-2 py-0.5 font-medium text-destructive">
                    {tFeed(`categories.${complaint.category}`)}
                  </span>
                  <span className="text-muted-foreground">
                    {t(`stages.${complaint.stage}`)} ·{" "}
                    {complaint.source_type}
                  </span>
                  {complaint.got_offer !== null && (
                    <span className="rounded-md bg-secondary px-2 py-0.5">
                      {complaint.got_offer ? t("offerYes") : t("offerNo")}
                    </span>
                  )}
                  {complaint.difficulty !== null && (
                    <span className="rounded-md bg-secondary px-2 py-0.5">
                      {t("difficultyChip", { value: complaint.difficulty })}
                    </span>
                  )}
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
                <EvidenceLinks items={complaint.evidence} />
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
                <div className="mt-3 flex items-center gap-2 border-t border-border pt-2.5">
                  <HelpfulButton
                    companyId={id}
                    kind="complaints"
                    postId={complaint.id}
                    initialCount={complaint.helpful_count}
                  />
                  <CommentsSection
                    companyId={id}
                    kind="complaints"
                    postId={complaint.id}
                  />
                  <ShareButton companyId={id} />
                </div>
                <ModeratorTools
                  targetKind="complaints"
                  targetId={complaint.id}
                />
              </article>
    );
  }
}
