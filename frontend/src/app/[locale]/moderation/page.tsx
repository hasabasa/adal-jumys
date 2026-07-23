import { getTranslations, setRequestLocale } from "next-intl/server";

import { Button } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { getModerationLog, getOverturnStats } from "@/lib/api";

// Ашық аудит-лог: модерация да ашық - платформаның сенім-қағидасы
export default async function ModerationPage({
  params,
}: Readonly<{ params: Promise<{ locale: string }> }>) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("moderation");
  const [log, stats] = await Promise.all([
    getModerationLog(),
    getOverturnStats(),
  ]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{t("title")}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t("subtitle")}</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          render={<Link href="/moderation/panel" />}
        >
          {t("panelLink")}
        </Button>
      </div>

      {stats.length > 0 && (
        <section className="mt-6">
          <h2 className="text-sm font-semibold">{t("statsTitle")}</h2>
          <div className="mt-2 overflow-x-auto rounded-xl border border-border">
            <table className="w-full text-sm">
              <thead className="bg-secondary text-left text-xs">
                <tr>
                  <th className="px-3 py-2">{t("statsModerator")}</th>
                  <th className="px-3 py-2">{t("statsActions")}</th>
                  <th className="px-3 py-2">{t("statsOverturned")}</th>
                </tr>
              </thead>
              <tbody>
                {stats.map((row) => (
                  <tr
                    key={row.moderator_pseudonym}
                    className="border-t border-border"
                  >
                    <td className="px-3 py-2">{row.moderator_pseudonym}</td>
                    <td className="px-3 py-2">{row.total_actions}</td>
                    <td className="px-3 py-2">{row.overturned}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="mt-8 pb-16">
        <h2 className="text-sm font-semibold">{t("logTitle")}</h2>
        {log.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">{t("logEmpty")}</p>
        ) : (
          <div className="mt-2 grid gap-2">
            {log.map((item) => (
              <div
                key={item.id}
                className="rounded-lg border border-border bg-card p-3 text-sm"
              >
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="font-medium">
                    {item.actor_pseudonym ?? t("system")}
                  </span>
                  <span className="rounded-md bg-secondary px-2 py-0.5">
                    {t(`actions.${item.action}`)}
                  </span>
                  <span className="text-muted-foreground">
                    {t(`targets.${item.target_type}`)}
                  </span>
                  <span className="ml-auto text-muted-foreground">
                    {new Date(item.created_at).toLocaleDateString(locale)}
                  </span>
                </div>
                <p className="mt-1.5 text-muted-foreground">{item.reason}</p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
