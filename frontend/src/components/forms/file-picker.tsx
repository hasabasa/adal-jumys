"use client";

import { useTranslations } from "next-intl";
import { useRef } from "react";

// Браузердің өз file-input-ы жасырылады (оның "Файл не выбран" жазуы
// браузер тіліне бағынып, аудармамызға көнбейді) - орнына өз UI-ымыз
export function FilePicker({
  files,
  onChange,
  multiple = false,
  accept,
  maxFiles = 5,
}: Readonly<{
  files: File[];
  onChange: (files: File[]) => void;
  multiple?: boolean;
  accept?: string;
  maxFiles?: number;
}>) {
  const t = useTranslations("filePicker");
  const inputRef = useRef<HTMLInputElement>(null);

  function addFiles(selected: FileList | null) {
    if (!selected) return;
    const merged = multiple
      ? [...files, ...Array.from(selected)].slice(0, maxFiles)
      : Array.from(selected).slice(0, 1);
    onChange(merged);
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        multiple={multiple}
        accept={accept}
        className="hidden"
        onChange={(event) => {
          addFiles(event.target.files);
          event.target.value = "";
        }}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="flex w-full flex-col items-center gap-1 rounded-lg border-2 border-dashed border-input bg-card py-5 transition-colors hover:border-primary hover:bg-accent/30"
      >
        <span className="text-base font-bold text-primary">
          {t("choose")}
        </span>
        <span className="text-xs text-muted-foreground">
          {files.length === 0
            ? t("empty")
            : t("count", { count: files.length })}
        </span>
      </button>

      {files.length > 0 && (
        <ul className="mt-2 grid gap-1">
          {files.map((file, index) => (
            <li
              key={`${file.name}-${index}`}
              className="flex items-center justify-between rounded-md bg-secondary px-3 py-1.5 text-xs"
            >
              <span className="truncate">{file.name}</span>
              <button
                type="button"
                onClick={() =>
                  onChange(files.filter((_, i) => i !== index))
                }
                className="ml-2 font-bold text-destructive hover:opacity-70"
                aria-label={t("remove")}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
