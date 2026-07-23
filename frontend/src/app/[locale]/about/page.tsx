import { getTranslations, setRequestLocale } from "next-intl/server";

// Болашақта осы бетке ғимарат-шоу (anime.js) қосылады
export default async function AboutPage({
  params,
}: Readonly<{ params: Promise<{ locale: string }> }>) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("about");

  const principles = [1, 2, 3, 4, 5, 6] as const;
  const steps = [1, 2, 3] as const;

  return (
    <div className="mx-auto max-w-3xl px-4 py-14">
      <h1 className="font-display text-3xl tracking-tight text-balance">
        {t("title")}
      </h1>
      <p className="mt-4 text-muted-foreground">{t("mission")}</p>
      <p className="mt-3 text-muted-foreground">{t("problem")}</p>

      <h2 className="mt-10 text-lg font-semibold">{t("howTitle")}</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {steps.map((step) => (
          <div
            key={step}
            className="rounded-xl border border-border bg-card p-4"
          >
            <div className="font-display text-xl text-primary">{step}</div>
            <p className="mt-2 text-sm">{t(`steps.${step}`)}</p>
          </div>
        ))}
      </div>

      <h2 className="mt-10 text-lg font-semibold">{t("principlesTitle")}</h2>
      <div className="mt-4 grid gap-3">
        {principles.map((index) => (
          <div
            key={index}
            className="rounded-xl border border-border bg-card p-4"
          >
            <p className="font-semibold">{t(`principles.${index}.title`)}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {t(`principles.${index}.body`)}
            </p>
          </div>
        ))}
      </div>

      <h2 className="mt-10 text-lg font-semibold">{t("openTitle")}</h2>
      <p className="mt-2 text-sm text-muted-foreground">{t("openBody")}</p>
      <p className="mt-2 text-sm">
        <a
          href="https://github.com/hasabasa/adal-jumys"
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:underline"
        >
          github.com/hasabasa/adal-jumys
        </a>{" "}
        ·{" "}
        <a
          href="https://t.me/baldween"
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:underline"
        >
          Telegram: @baldween
        </a>
      </p>
    </div>
  );
}
