"use client";

import { animate, stagger } from "animejs";
import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";

import { FeedCard } from "@/components/feed/feed-card";
import { getFeed, type FeedItem } from "@/lib/api";

const POLL_INTERVAL_MS = 60_000;

export function FeedList({
  initialItems,
}: Readonly<{ initialItems: FeedItem[] }>) {
  const t = useTranslations("feed");
  const [items, setItems] = useState(initialItems);
  const listRef = useRef<HTMLDivElement>(null);
  const knownIds = useRef(new Set(initialItems.map((item) => item.id)));

  // Алғашқы көрініс: карточкалар сатылап (stagger) көтеріліп шығады
  useEffect(() => {
    if (!listRef.current) return;
    animate(listRef.current.children, {
      opacity: [0, 1],
      translateY: [16, 0],
      delay: stagger(70),
      duration: 450,
      ease: "outQuad",
    });
  }, []);

  // Әр минутта жаңасын тексеру: жаңа пост үстінен сырғып түседі
  useEffect(() => {
    const timer = setInterval(async () => {
      const fresh = await getFeed();
      const newOnes = fresh.filter((item) => !knownIds.current.has(item.id));
      if (newOnes.length === 0) return;
      for (const item of fresh) knownIds.current.add(item.id);
      setItems(fresh);
      requestAnimationFrame(() => {
        if (!listRef.current) return;
        animate(Array.from(listRef.current.children).slice(0, newOnes.length), {
          opacity: [0, 1],
          translateY: [-20, 0],
          delay: stagger(90),
          duration: 500,
          ease: "outQuad",
        });
      });
    }, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, []);

  if (items.length === 0) {
    return (
      <div className="flex h-24 items-center justify-center rounded-xl border border-dashed border-border text-sm text-muted-foreground">
        {t("empty")}
      </div>
    );
  }

  return (
    <div ref={listRef} className="grid gap-3">
      {items.map((item) => (
        <FeedCard key={item.id} item={item} />
      ))}
    </div>
  );
}
