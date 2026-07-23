import { getTranslations, setRequestLocale } from "next-intl/server";

export default async function FaqPage({
  params,
}: Readonly<{ params: Promise<{ locale: string }> }>) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("faq");

  const items = [1, 2, 3, 4, 5, 6, 7] as const;

  return (
    <div className="mx-auto max-w-3xl px-4 py-14">
      <h1 className="font-display text-3xl tracking-tight text-balance">
        {t("title")}
      </h1>
      <p className="mt-4 text-muted-foreground">{t("intro")}</p>

      <div className="mt-8 grid gap-2">
        {items.map((index) => (
          <details
            key={index}
            className="group rounded-xl border border-border bg-card p-4"
          >
            <summary className="cursor-pointer list-none font-semibold marker:hidden">
              <span className="mr-2 text-primary group-open:hidden">+</span>
              <span className="mr-2 hidden text-primary group-open:inline">
                −
              </span>
              {t(`items.${index}.q`)}
            </summary>
            <p className="mt-2 text-sm text-muted-foreground">
              {t(`items.${index}.a`)}
            </p>
          </details>
        ))}
      </div>
    </div>
  );
}
