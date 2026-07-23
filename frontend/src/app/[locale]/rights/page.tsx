import { getTranslations, setRequestLocale } from "next-intl/server";

// docs/categories.md каталогынан: категория -> ЕК-бабы
const CATEGORY_ARTICLES: [string, string][] = [
  ["unpaid_salary", "ЕК 113"],
  ["delayed_salary", "ЕК 113"],
  ["no_pension_contributions", ""],
  ["unpaid_overtime", "ЕК 78, 108"],
  ["unpaid_holiday_work", "ЕК 109"],
  ["no_contract", "ЕК 33"],
  ["illegal_fines", "ЕК 115"],
  ["no_vacation", "ЕК 88"],
  ["no_sick_leave", "ЕК 133"],
  ["unsafe_conditions", "ЕК 182"],
  ["illegal_dismissal", "ЕК 52, 54"],
  ["no_final_settlement", "ЕК 113"],
  ["forced_labor", "ЕК 7"],
];

export default async function RightsPage({
  params,
}: Readonly<{ params: Promise<{ locale: string }> }>) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("rights");
  const tProblems = await getTranslations("problems");

  return (
    <div className="mx-auto max-w-3xl px-4 py-14">
      <h1 className="font-display text-3xl tracking-tight text-balance">
        {t("title")}
      </h1>
      <p className="mt-4 text-muted-foreground">{t("intro")}</p>

      <div className="mt-8 overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead className="bg-secondary text-left text-xs">
            <tr>
              <th className="px-4 py-2.5">{t("columnViolation")}</th>
              <th className="px-4 py-2.5">{t("columnLaw")}</th>
              <th className="px-4 py-2.5">{t("columnMeaning")}</th>
            </tr>
          </thead>
          <tbody>
            {CATEGORY_ARTICLES.map(([key, article]) => (
              <tr key={key} className="border-t border-border">
                <td className="px-4 py-2.5 font-medium">{tProblems(key)}</td>
                <td className="px-4 py-2.5 whitespace-nowrap text-primary">
                  {article || t("pensionLaw")}
                </td>
                <td className="px-4 py-2.5 text-muted-foreground">
                  {t(`meanings.${key}`)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 rounded-xl border border-dashed border-border p-4">
        <p className="text-sm font-semibold">{t("tipsTitle")}</p>
        <p className="mt-1 text-xs text-muted-foreground">{t("tipsSoon")}</p>
      </div>

      <p className="mt-6 text-xs text-muted-foreground">{t("disclaimer")}</p>
    </div>
  );
}
