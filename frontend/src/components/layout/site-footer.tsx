import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

export function SiteFooter() {
  const t = useTranslations("footer");

  const columns = [
    {
      title: t("aboutTitle"),
      links: [
        { label: t("about"), href: "/about" },
        { label: t("moderation"), href: "/moderation" },
        { label: t("forCompanies"), href: "/for-companies" },
      ],
    },
    {
      title: t("rightsTitle"),
      links: [
        { label: t("tips"), href: "/rights" },
        { label: t("faq"), href: "/faq" },
      ],
    },
  ];

  return (
    <footer className="border-t border-border bg-card">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:grid-cols-2 lg:grid-cols-4">
        {columns.map((column) => (
          <div key={column.title}>
            <h3 className="mb-3 text-sm font-semibold">{column.title}</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              {column.links.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="transition-colors hover:text-foreground"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}

        <div>
          <h3 className="mb-3 text-sm font-semibold">{t("devTitle")}</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>
              <a
                href="https://github.com/hasabasa/adal-jumys"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors hover:text-foreground"
              >
                {t("github")}
              </a>
            </li>
            <li>
              <a
                href="http://localhost:8000/docs"
                className="transition-colors hover:text-foreground"
              >
                {t("api")}
              </a>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="mb-3 text-sm font-semibold">{t("contactTitle")}</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>Хасенхан</li>
            <li>
              <a
                href="https://t.me/baldween"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors hover:text-foreground"
              >
                Telegram: @baldween
              </a>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col gap-1 px-4 py-4 text-xs text-muted-foreground sm:flex-row sm:justify-between">
          <span>{t("license")}</span>
          <span>{t("principle")}</span>
        </div>
      </div>
    </footer>
  );
}
