"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { clearToken, fetchCurrentUser, type CurrentUser } from "@/lib/auth";

export function AuthStatus() {
  const t = useTranslations("nav");
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    const refresh = () => {
      fetchCurrentUser().then(setUser);
    };
    refresh();
    window.addEventListener("adal-auth-changed", refresh);
    return () => window.removeEventListener("adal-auth-changed", refresh);
  }, []);

  if (user === null) {
    return (
      <Button size="sm" render={<Link href="/login" />}>
        {t("login")}
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="font-medium">{user.pseudonym}</span>
      <Button size="sm" variant="outline" onClick={() => clearToken()}>
        {t("logout")}
      </Button>
    </div>
  );
}
