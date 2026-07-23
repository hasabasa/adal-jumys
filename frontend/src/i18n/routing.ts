import { defineRouting } from "next-intl/routing";

// Qazaq-first: kk - әдепкі тіл
export const routing = defineRouting({
  locales: ["kk", "ru"],
  defaultLocale: "kk",
});
