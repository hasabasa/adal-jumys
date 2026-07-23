import type { Metadata } from "next";
import { hasLocale, NextIntlClientProvider } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { Golos_Text } from "next/font/google";
import { notFound } from "next/navigation";

import "../globals.css";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { routing } from "@/i18n/routing";

// Golos Text: кириллица үшін арнайы сызылған - қазақ әріптері (ӘҒҚҢӨҰҮҺІ)
// туған glyphs ретінде салынған. Glassdoor/kununu үлгісі: бір отбасы,
// тақырыптар салмақ-контрастпен (800) ерекшеленеді
const golos = Golos_Text({
  variable: "--font-golos",
  subsets: ["latin", "cyrillic", "cyrillic-ext"],
});

export const metadata: Metadata = {
  title: "Adal Jumys — еңбек нарығының ашықтық платформасы",
  description:
    "Жұмыс берушіңді алдын ала тексер: рейтингтер, верифицирленген отзывтар, вакансия-шағымдар. Қазақстан.",
};

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}>) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }
  setRequestLocale(locale);

  return (
    <html lang={locale} className={`${golos.variable} h-full antialiased`}>
      <body className="flex min-h-screen flex-col font-sans">
        <NextIntlClientProvider>
          <SiteHeader />
          <main className="flex-1">{children}</main>
          <SiteFooter />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
