"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { useRouter } from "@/i18n/navigation";
import { post } from "@/lib/api";
import { fetchCurrentUser, getToken, type CurrentUser } from "@/lib/auth";

// Бір беттегі барлық карточка бір ғана /auth/me сұранысын бөліседі
let cachedUser: Promise<CurrentUser | null> | null = null;
function currentUserOnce(): Promise<CurrentUser | null> {
  cachedUser ??= fetchCurrentUser();
  return cachedUser;
}

export function ModeratorTools({
  targetKind,
  targetId,
}: Readonly<{ targetKind: "reviews" | "complaints"; targetId: string }>) {
  const t = useTranslations("moderation");
  const router = useRouter();
  const [isModerator, setIsModerator] = useState(false);
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    currentUserOnce().then((user) => {
      setIsModerator(
        user !== null &&
          (user.trust_level === "moderator" || user.trust_level === "admin"),
      );
    });
  }, []);

  if (!isModerator) return null;

  async function onHide() {
    setBusy(true);
    setError(null);
    try {
      await post(
        `/moderation/${targetKind}/${targetId}/hide`,
        { reason },
        getToken(),
      );
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Қате");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-2 border-t border-dashed border-border pt-2">
      {open ? (
        <div className="flex flex-wrap items-center gap-2">
          <input
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder={t("reasonPlaceholder")}
            className="h-8 min-w-48 flex-1 rounded-lg border border-input bg-card px-2 text-xs"
          />
          <Button
            size="sm"
            variant="destructive"
            disabled={reason.trim().length < 10 || busy}
            onClick={onHide}
          >
            {t("hide")}
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setOpen(false)}>
            {t("cancel")}
          </Button>
          {error && <span className="text-xs text-destructive">{error}</span>}
        </div>
      ) : (
        <button
          onClick={() => setOpen(true)}
          className="text-xs text-muted-foreground hover:text-destructive"
        >
          {t("hide")}
        </button>
      )}
    </div>
  );
}
