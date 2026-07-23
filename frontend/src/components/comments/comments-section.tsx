"use client";

import { MessageCircle } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { Avatar } from "@/components/feed/avatar";
import { Button } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { getComments, post, type PostComment } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { relativeTime } from "@/lib/format";

export function CommentsSection({
  companyId,
  kind,
  postId,
}: Readonly<{
  companyId: string;
  kind: "reviews" | "complaints";
  postId: string;
}>) {
  const t = useTranslations("comments");
  const locale = useLocale();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<PostComment[] | null>(null);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(getToken() !== null);
  }, []);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && items === null) {
      setItems(await getComments(companyId, kind, postId));
    }
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const created = await post<PostComment>(
        `/companies/${companyId}/${kind}/${postId}/comments`,
        { body },
        getToken(),
      );
      setItems([...(items ?? []), created]);
      setBody("");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("genericError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={toggle}
        aria-label={t("title")}
        title={t("title")}
        className={`flex items-center gap-1.5 rounded-full p-1.5 transition-colors hover:bg-accent/50 hover:text-primary ${
          open ? "text-primary" : "text-muted-foreground"
        }`}
      >
        <MessageCircle className="size-[18px]" strokeWidth={1.8} />
        {items !== null && items.length > 0 && (
          <span className="text-xs font-medium">{items.length}</span>
        )}
      </button>

      {open && (
        <div className="mt-3 border-l-2 border-border pl-3">
          {items === null ? (
            <p className="text-xs text-muted-foreground">...</p>
          ) : items.length === 0 ? (
            <p className="text-xs text-muted-foreground">{t("empty")}</p>
          ) : (
            <ul className="grid gap-2.5">
              {items.map((comment) => (
                <li key={comment.id} className="flex gap-2">
                  <div className="scale-75 origin-top-left">
                    <Avatar name={comment.author_pseudonym} />
                  </div>
                  <div className="min-w-0 -ml-1.5">
                    <p className="text-xs">
                      <span className="font-semibold">
                        {comment.author_pseudonym}
                      </span>{" "}
                      <span className="text-muted-foreground">
                        {relativeTime(comment.created_at, locale)}
                      </span>
                    </p>
                    <p className="text-sm">{comment.body}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {authed ? (
            <form onSubmit={onSubmit} className="mt-3 flex gap-2">
              <input
                value={body}
                onChange={(event) => setBody(event.target.value)}
                minLength={2}
                maxLength={1000}
                required
                placeholder={t("placeholder")}
                className="h-9 flex-1 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              />
              <Button type="submit" size="sm" disabled={busy}>
                {busy ? "..." : t("submit")}
              </Button>
            </form>
          ) : (
            <p className="mt-3 text-xs text-muted-foreground">
              <Link href="/login" className="text-primary hover:underline">
                {t("loginPrompt")}
              </Link>
            </p>
          )}
          {error && <p className="mt-1 text-xs text-destructive">{error}</p>}
        </div>
      )}
    </div>
  );
}
