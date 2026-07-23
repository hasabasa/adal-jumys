"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Link, useRouter } from "@/i18n/navigation";
import { login } from "@/lib/auth";

export default function LoginPage() {
  const t = useTranslations("auth");
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      await login(String(form.get("email")), String(form.get("password")));
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("genericError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-sm flex-col px-4 py-16">
      <h1 className="text-2xl font-bold">{t("loginTitle")}</h1>
      <form onSubmit={onSubmit} className="mt-6 grid gap-3">
        <input
          name="email"
          type="email"
          required
          placeholder={t("email")}
          className="h-10 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        <input
          name="password"
          type="password"
          required
          minLength={8}
          placeholder={t("password")}
          className="h-10 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" disabled={busy}>
          {busy ? "..." : t("loginButton")}
        </Button>
      </form>
      <p className="mt-4 text-sm text-muted-foreground">
        {t("noAccount")}{" "}
        <Link href="/register" className="text-primary hover:underline">
          {t("registerLink")}
        </Link>
      </p>
    </div>
  );
}
