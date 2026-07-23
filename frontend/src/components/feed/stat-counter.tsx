"use client";

import { animate } from "animejs";
import { useEffect, useRef } from "react";

export function StatCounter({ value }: Readonly<{ value: number }>) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const counter = { n: 0 };
    animate(counter, {
      n: value,
      duration: 1200,
      ease: "outExpo",
      onUpdate: () => {
        el.textContent = Math.round(counter.n).toLocaleString("kk-KZ");
      },
    });
  }, [value]);

  return <span ref={ref}>0</span>;
}
