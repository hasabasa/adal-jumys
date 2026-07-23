import { defineRouting } from "next-intl/routing";

// Qazaq-first: сайт ӘРҚАШАН қазақша ашылады (браузер тіліне қарамай),
// тіл тек юзер өзі ауыстырғанда өзгереді (таңдауы cookie-де сақталады)
export const routing = defineRouting({
  locales: ["kk", "ru"],
  defaultLocale: "kk",
  localeDetection: false,
});
