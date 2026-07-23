import { getTranslations, setRequestLocale } from "next-intl/server";

import { Button } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { getCompanies } from "@/lib/api";

export default async function CompaniesPage({
  params,
  searchParams,
}: Readonly<{
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ search?: string }>;
}>) {
  const { locale } = await params;
  setRequestLocale(locale);
  const { search } = await searchParams;
  const t = await getTranslations("companies");
  const companies = await getCompanies(search ?? null);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <Button render={<Link href="/companies/new" />} variant="outline">
          {t("addCompany")}
        </Button>
      </div>

      <form action="" className="mt-5 flex gap-2">
        <input
          type="search"
          name="search"
          defaultValue={search ?? ""}
          placeholder={t("searchPlaceholder")}
          className="h-10 flex-1 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        <Button type="submit">{t("searchButton")}</Button>
      </form>

      {companies.length === 0 ? (
        <div className="mt-8 flex flex-col items-center gap-3 rounded-xl border border-dashed border-border py-12 text-center">
          <p className="text-sm text-muted-foreground">{t("empty")}</p>
          <Button render={<Link href="/companies/new" />}>
            {t("addCompany")}
          </Button>
        </div>
      ) : (
        <div className="mt-6 grid gap-3">
          {companies.map((company) => (
            <Link
              key={company.id}
              href={`/companies/${company.id}`}
              className="rounded-xl border border-border bg-card p-4 transition-colors hover:border-ring/40"
            >
              <div className="flex items-center justify-between gap-3">
                <h2 className="font-semibold">{company.name}</h2>
                <span className="text-xs text-muted-foreground">
                  {t("bin")}: {company.bin}
                </span>
              </div>
              {company.city && (
                <p className="mt-1 text-sm text-muted-foreground">
                  {company.city}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
