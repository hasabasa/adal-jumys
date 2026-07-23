"use client";

import { useLocale, useTranslations } from "next-intl";

import { AuthStatus } from "@/components/layout/auth-status";
import { Link, usePathname } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";
import { cn } from "@/lib/utils";

export function SiteHeader() {
  const t = useTranslations("nav");
  const locale = useLocale();
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-6 px-4">
        <Link href="/" className="flex items-center gap-1.5 font-semibold">
          <span className="size-2.5 rounded-full bg-primary" aria-hidden />
          Adal Jumys
        </Link>

        <nav className="hidden items-center gap-5 text-sm text-muted-foreground sm:flex">
          <Link href="/companies" className="transition-colors hover:text-foreground">
            {t("companies")}
          </Link>
          <Link href="/rights" className="transition-colors hover:text-foreground">
            {t("rights")}
          </Link>
          <Link href="/about" className="transition-colors hover:text-foreground">
            {t("about")}
          </Link>
        </nav>

        <div className="ml-auto flex items-center gap-3">
          <div className="flex items-center rounded-lg border border-border p-0.5 text-xs">
            {routing.locales.map((code) => (
              <Link
                key={code}
                href={pathname}
                locale={code}
                className={cn(
                  "rounded-md px-2 py-1 uppercase transition-colors",
                  code === locale
                    ? "bg-secondary font-semibold text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {code}
              </Link>
            ))}
          </div>
          <AuthStatus />
        </div>
      </div>
    </header>
  );
}
