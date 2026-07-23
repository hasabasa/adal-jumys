"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";

export function ShareButton({ companyId }: Readonly<{ companyId: string }>) {
  const t = useTranslations("feed");
  const locale = useLocale();
  const [copied, setCopied] = useState(false);

  async function onShare() {
    const url = `${window.location.origin}/${locale}/companies/${companyId}`;
    if (navigator.share) {
      try {
        await navigator.share({ url });
        return;
      } catch {
        // юзер бөлісуден бас тартты - үнсіз өтеміз
      }
    }
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <button
      type="button"
      onClick={onShare}
      className="text-xs text-muted-foreground transition-colors hover:text-primary"
    >
      {copied ? t("copied") : `↗ ${t("share")}`}
    </button>
  );
}
