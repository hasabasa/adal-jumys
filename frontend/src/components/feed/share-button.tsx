"use client";

import { Check, Share2 } from "lucide-react";
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
      aria-label={t("share")}
      title={t("share")}
      className="flex items-center gap-1.5 rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-accent/50 hover:text-primary"
    >
      {copied ? (
        <>
          <Check className="size-[18px] text-success" />
          <span className="text-xs text-success">{t("copied")}</span>
        </>
      ) : (
        <Share2 className="size-[18px]" strokeWidth={1.8} />
      )}
    </button>
  );
}
