// Бүркеншік атқа тұрақты түс: аты өзгермесе түсі де өзгермейді
function hueOf(name: string): number {
  let hash = 0;
  for (const char of name) {
    hash = (hash * 31 + char.charCodeAt(0)) % 360;
  }
  return hash;
}

export function Avatar({ name }: Readonly<{ name: string }>) {
  const hue = hueOf(name);
  return (
    <span
      aria-hidden
      className="flex size-9 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white"
      style={{ backgroundColor: `oklch(0.6 0.13 ${hue})` }}
    >
      {name.charAt(0).toUpperCase()}
    </span>
  );
}
