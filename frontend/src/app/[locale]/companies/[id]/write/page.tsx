import { getTranslations, setRequestLocale } from "next-intl/server";

import { Link } from "@/i18n/navigation";

// Бір кіру нүктесі: юзер "пікір ме, шағым ба" деп бас қатырмайды -
// адам тілімен бір сұрақ, жауабына қарай тиісті форма ашылады
export default async function WritePage({
  params,
}: Readonly<{ params: Promise<{ locale: string; id: string }> }>) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("write");

  return (
    <div className="mx-auto max-w-lg px-4 py-16">
      <h1 className="text-center text-2xl font-bold text-balance">
        {t("question")}
      </h1>

      <div className="mt-8 grid gap-3">
        <Link
          href={`/companies/${id}/review`}
          className="rounded-xl border-2 border-border bg-card p-5 transition-colors hover:border-primary"
        >
          <p className="font-semibold">{t("workerTitle")}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("workerDescription")}
          </p>
        </Link>

        <Link
          href={`/companies/${id}/complain`}
          className="rounded-xl border-2 border-border bg-card p-5 transition-colors hover:border-primary"
        >
          <p className="font-semibold">{t("candidateTitle")}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("candidateDescription")}
          </p>
        </Link>
      </div>
    </div>
  );
}
