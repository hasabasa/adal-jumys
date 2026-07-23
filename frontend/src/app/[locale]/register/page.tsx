"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Link, useRouter } from "@/i18n/navigation";
import { register } from "@/lib/auth";
import { cn } from "@/lib/utils";

export default function RegisterPage() {
  const t = useTranslations("auth");
  const router = useRouter();
  const [role, setRole] = useState<"worker" | "company">("worker");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      await register({
        email: String(form.get("email")),
        password: String(form.get("password")),
        pseudonym: String(form.get("pseudonym")),
        role,
      });
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("genericError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-sm flex-col px-4 py-16">
      <h1 className="text-2xl font-bold">{t("registerTitle")}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{t("privacyNote")}</p>

      <form onSubmit={onSubmit} className="mt-6 grid gap-3">
        <div className="grid grid-cols-2 gap-2">
          {(["worker", "company"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setRole(value)}
              className={cn(
                "h-10 rounded-lg border text-sm font-medium transition-colors",
                role === value
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border text-muted-foreground hover:text-foreground",
              )}
            >
              {t(`role_${value}`)}
            </button>
          ))}
        </div>
        <input
          name="email"
          type="email"
          required
          placeholder={t("email")}
          className="h-10 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        <input
          name="pseudonym"
          required
          minLength={3}
          maxLength={30}
          pattern="[a-zA-Z0-9_Ѐ-ӿӘәҒғҚқҢңӨөҰұҮүҺһІі]+"
          placeholder={t("pseudonym")}
          className="h-10 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        <p className="text-xs text-muted-foreground">{t("pseudonymHint")}</p>
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
          {busy ? "..." : t("registerButton")}
        </Button>
      </form>

      <p className="mt-4 text-sm text-muted-foreground">
        {t("haveAccount")}{" "}
        <Link href="/login" className="text-primary hover:underline">
          {t("loginLink")}
        </Link>
      </p>
    </div>
  );
}
