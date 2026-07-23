"use client";

import { ThumbsUp } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { post } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { cn } from "@/lib/utils";

export function HelpfulButton({
  companyId,
  kind,
  postId,
  initialCount,
}: Readonly<{
  companyId: string;
  kind: "reviews" | "complaints";
  postId: string;
  initialCount: number;
}>) {
  const t = useTranslations("feed");
  const [count, setCount] = useState(initialCount);
  const [voted, setVoted] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onToggle() {
    if (getToken() === null) return;
    setBusy(true);
    try {
      const state = await post<{ count: number; voted: boolean }>(
        `/companies/${companyId}/${kind}/${postId}/helpful`,
        {},
        getToken(),
      );
      setCount(state.count);
      setVoted(state.voted);
    } catch {
      // лимитке тірелсе/қате болса үнсіз өтеміз
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={busy}
      aria-label={t("helpful")}
      title={t("helpful")}
      className={cn(
        "flex items-center gap-1.5 rounded-full p-1.5 transition-colors hover:bg-accent/50 hover:text-primary",
        voted ? "text-primary" : "text-muted-foreground",
      )}
    >
      <ThumbsUp
        className="size-[18px]"
        strokeWidth={1.8}
        fill={voted ? "currentColor" : "none"}
      />
      {count > 0 && <span className="text-xs font-medium">{count}</span>}
    </button>
  );
}
