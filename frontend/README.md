# Adal Jumys frontend

Платформаның веб-интерфейсі: Next.js 16 (App Router), TypeScript, Tailwind v4, next-intl (qazaq-first: kk әдепкі / ru), anime.js.

# Іске қосу

```bash
pnpm install
pnpm dev
```

Браузерде: `http://localhost:3000` (автоматты `/kk`-ға бағыттайды).

Толық жұмысқа backend API да қосулы болуы керек (`../backend`, 8000-порт) — нұсқаулық репоның басты README-інде.

# Құрылым

- `src/app/[locale]/` - беттер (kk/ru екеуіне бір код)
- `src/components/layout/` - хедер, футер
- `src/components/ui/` - shadcn/ui компоненттері
- `src/i18n/` - тіл-баптау (kk әдепкі)
- `messages/` - аудармалар (kk.json, ru.json)
- `src/app/globals.css` - дизайн-токендер: бүкіл палитра осы жерде өзгертіледі
- `src/proxy.ts` - тіл-бағыттау (Next 16-да middleware осылай аталады)
