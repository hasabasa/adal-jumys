"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useRouter } from "@/i18n/navigation";
import { post, lookupBin, type Company } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function NewCompanyPage() {
  const t = useTranslations("companies");
  const router = useRouter();
  const [bin, setBin] = useState("");
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [address, setAddress] = useState("");
  const [twoGis, setTwoGis] = useState("");
  const [website, setWebsite] = useState("");
  const [instagram, setInstagram] = useState("");
  const [lookupState, setLookupState] = useState<"idle" | "busy" | "notfound">(
    "idle",
  );
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onLookup() {
    setLookupState("busy");
    const info = await lookupBin(bin);
    if (info === null) {
      setLookupState("notfound");
      return;
    }
    setName(info.name);
    if (info.address) setAddress(info.address);
    setLookupState("idle");
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const company = await post<Company>(
        "/companies",
        {
          bin,
          name,
          city: city || null,
          address: address || null,
          two_gis_url: twoGis || null,
          website: website || null,
          instagram_url: instagram || null,
        },
        getToken(),
      );
      router.push(`/companies/${company.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("genericError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm px-4 py-16">
      <h1 className="text-2xl font-bold">{t("addCompany")}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{t("newHint")}</p>

      <form onSubmit={onSubmit} className="mt-6 grid gap-3">
        <div className="flex gap-2">
          <input
            value={bin}
            onChange={(event) => setBin(event.target.value)}
            required
            pattern="\d{12}"
            placeholder={t("binPlaceholder")}
            className="h-10 flex-1 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          />
          <Button
            type="button"
            variant="outline"
            onClick={onLookup}
            disabled={bin.length !== 12 || lookupState === "busy"}
          >
            {lookupState === "busy" ? "..." : t("lookupButton")}
          </Button>
        </div>
        {lookupState === "notfound" && (
          <p className="text-xs text-muted-foreground">{t("lookupNotFound")}</p>
        )}
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
          minLength={2}
          placeholder={t("namePlaceholder")}
          className="h-10 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        <input
          value={city}
          onChange={(event) => setCity(event.target.value)}
          placeholder={t("cityPlaceholder")}
          className="h-10 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        <input
          value={address}
          onChange={(event) => setAddress(event.target.value)}
          placeholder={t("addressPlaceholder")}
          className="h-10 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        <input
          value={twoGis}
          onChange={(event) => setTwoGis(event.target.value)}
          type="url"
          placeholder={t("twoGisPlaceholder")}
          className="h-10 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        <input
          value={website}
          onChange={(event) => setWebsite(event.target.value)}
          type="url"
          placeholder={t("websitePlaceholder")}
          className="h-10 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        <input
          value={instagram}
          onChange={(event) => setInstagram(event.target.value)}
          type="url"
          placeholder={t("instagramPlaceholder")}
          className="h-10 rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        <p className="text-xs text-muted-foreground">{t("officialOnlyHint")}</p>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" disabled={busy}>
          {busy ? "..." : t("createButton")}
        </Button>
      </form>
    </div>
  );
}
