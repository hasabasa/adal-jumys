"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { representationStatus } from "@/components/company/represent-button";
import { Button } from "@/components/ui/button";
import { useRouter } from "@/i18n/navigation";
import { post } from "@/lib/api";
import { getToken } from "@/lib/auth";

export function RespondButton({
  companyId,
  kind,
  postId,
  hasResponse,
}: Readonly<{
  companyId: string;
  kind: "reviews" | "complaints";
  postId: string;
  hasResponse: boolean;
}>) {
  const t = useTranslations("represent");
  const router = useRouter();
  const [approved, setApproved] = useState(false);
  const [open, setOpen] = useState(false);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (getToken() === null || hasResponse) return;
    representationStatus(companyId).then((status) =>
      setApproved(status === "approved"),
    );
  }, [companyId, hasResponse]);

  if (!approved || hasResponse) return null;

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await post(
        `/companies/${companyId}/${kind}/${postId}/response`,
        { body },
        getToken(),
      );
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("genericError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-2">
      {open ? (
        <form onSubmit={onSubmit} className="grid gap-2">
          <textarea
            value={body}
            onChange={(event) => setBody(event.target.value)}
            required
            minLength={20}
            maxLength={5000}
            rows={3}
            placeholder={t("respondPlaceholder")}
            className="rounded-lg border border-input bg-card px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          />
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={busy}>
              {busy ? "..." : t("respondSubmit")}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setOpen(false)}
            >
              {t("cancel")}
            </Button>
          </div>
          {error && <p className="text-xs text-destructive">{error}</p>}
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="text-xs font-medium text-primary hover:underline"
        >
          {t("respondButton")}
        </button>
      )}
    </div>
  );
}
