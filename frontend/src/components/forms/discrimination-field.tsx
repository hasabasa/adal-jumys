"use client";

import { useTranslations } from "next-intl";

export type DiscriminationValue = {
  enabled: boolean;
  kind: string;
  form: string;
  description: string;
};

export const EMPTY_DISCRIMINATION: DiscriminationValue = {
  enabled: false,
  kind: "language",
  form: "interview",
  description: "",
};

const KINDS = ["language", "age", "gender", "ethnicity", "other"];
const FORMS = ["vacancy_text", "interview", "at_work"];

export function DiscriminationField({
  value,
  onChange,
  required,
}: Readonly<{
  value: DiscriminationValue;
  onChange: (value: DiscriminationValue) => void;
  required?: boolean;
}>) {
  const t = useTranslations("discr");

  return (
    <div className="rounded-lg border border-border p-3">
      <label className="flex items-center gap-2 text-sm font-medium">
        <input
          type="checkbox"
          checked={value.enabled || Boolean(required)}
          disabled={required}
          onChange={(event) =>
            onChange({ ...value, enabled: event.target.checked })
          }
        />
        {t("toggle")}
      </label>

      {(value.enabled || required) && (
        <div className="mt-3 grid gap-2">
          <select
            value={value.kind}
            onChange={(event) => onChange({ ...value, kind: event.target.value })}
            className="h-10 rounded-lg border border-input bg-card px-2 text-sm"
          >
            {KINDS.map((kind) => (
              <option key={kind} value={kind}>
                {t(`kinds.${kind}`)}
              </option>
            ))}
          </select>
          <select
            value={value.form}
            onChange={(event) => onChange({ ...value, form: event.target.value })}
            className="h-10 rounded-lg border border-input bg-card px-2 text-sm"
          >
            {FORMS.map((form) => (
              <option key={form} value={form}>
                {t(`forms.${form}`)}
              </option>
            ))}
          </select>
          <textarea
            value={value.description}
            onChange={(event) =>
              onChange({ ...value, description: event.target.value })
            }
            maxLength={2000}
            rows={2}
            placeholder={t("descriptionPlaceholder")}
            className="rounded-lg border border-input bg-card px-3 py-2 text-sm"
          />
        </div>
      )}
    </div>
  );
}

export function toApiBlocks(value: DiscriminationValue, required?: boolean) {
  if (!value.enabled && !required) return [];
  return [
    {
      kind: value.kind,
      form: value.form,
      description: value.description || null,
    },
  ];
}
