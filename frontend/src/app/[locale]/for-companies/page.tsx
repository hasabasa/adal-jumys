import { getTranslations, setRequestLocale } from "next-intl/server";

import { Button } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";

export default async function ForCompaniesPage({
  params,
}: Readonly<{ params: Promise<{ locale: string }> }>) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("forCompanies");

  return (
    <div className="mx-auto max-w-3xl px-4 py-14">
      <h1 className="font-display text-3xl tracking-tight text-balance">
        {t("title")}
      </h1>
      <p className="mt-4 text-muted-foreground">{t("intro")}</p>

      <div className="mt-8 grid gap-4">
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="font-semibold">{t("replyTitle")}</h2>
          <p className="mt-2 text-sm text-muted-foreground">{t("replyBody")}</p>
          <ol className="mt-3 grid gap-1.5 text-sm">
            <li>1. {t("replyStep1")}</li>
            <li>2. {t("replyStep2")}</li>
            <li>3. {t("replyStep3")}</li>
          </ol>
        </section>

        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="font-semibold">{t("disputeTitle")}</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {t("disputeBody")}
          </p>
          <ol className="mt-3 grid gap-1.5 text-sm">
            <li>1. {t("disputeStep1")}</li>
            <li>2. {t("disputeStep2")}</li>
            <li>3. {t("disputeStep3")}</li>
          </ol>
        </section>

        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="font-semibold">{t("rulesTitle")}</h2>
          <ul className="mt-2 grid gap-1.5 text-sm text-muted-foreground">
            <li>{t("rule1")}</li>
            <li>{t("rule2")}</li>
            <li>{t("rule3")}</li>
          </ul>
        </section>
      </div>

      <div className="mt-8">
        <Button render={<Link href="/companies" />}>{t("cta")}</Button>
      </div>
    </div>
  );
}
