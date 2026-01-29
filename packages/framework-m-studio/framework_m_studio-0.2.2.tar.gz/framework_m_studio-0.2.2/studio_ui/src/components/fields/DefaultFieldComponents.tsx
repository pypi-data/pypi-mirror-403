/**
 * Default Field Components
 *
 * Provides default React components for built-in field types.
 * These are used as fallbacks when no custom component is registered.
 */

import { type FieldComponentProps } from "../../registry/fieldComponents";

// Input class styles
const inputClasses = "w-full px-3 py-2 rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 bg-white dark:bg-zinc-800 border-gray-200 dark:border-zinc-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500";

const checkboxClasses = "rounded border-gray-300 dark:border-zinc-600 text-blue-600 focus:ring-blue-500";

/**
 * Default Text Input Component
 */
export function DefaultTextInput({
  value,
  onChange,
  disabled,
  description,
}: FieldComponentProps) {
  return (
    <input
      type="text"
      value={String(value ?? "")}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      placeholder={description}
      className={inputClasses}
    />
  );
}

/**
 * Default Textarea Component (for long text)
 */
export function DefaultTextArea({
  value,
  onChange,
  disabled,
  description,
}: FieldComponentProps) {
  return (
    <textarea
      value={String(value ?? "")}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      placeholder={description}
      rows={4}
      className={inputClasses}
    />
  );
}

/**
 * Default Number Input Component
 */
export function DefaultNumberInput({
  value,
  onChange,
  disabled,
  schema,
}: FieldComponentProps) {
  const step = schema?.type === "float" ? "0.01" : "1";

  return (
    <input
      type="number"
      value={value !== undefined ? String(value) : ""}
      onChange={(e) => {
        const val = e.target.value;
        if (val === "") {
          onChange(undefined);
        } else {
          onChange(schema?.type === "float" ? parseFloat(val) : parseInt(val));
        }
      }}
      disabled={disabled}
      step={step}
      className={inputClasses}
    />
  );
}

/**
 * Default Checkbox Component
 */
export function DefaultCheckbox({
  value,
  onChange,
  disabled,
  fieldName,
}: FieldComponentProps) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={Boolean(value)}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className={checkboxClasses}
      />
      <span className="text-sm text-gray-700 dark:text-zinc-300">
        {fieldName}
      </span>
    </label>
  );
}

/**
 * Default Select Component
 */
export function DefaultSelect({
  value,
  onChange,
  disabled,
  schema,
}: FieldComponentProps) {
  const options = (schema?.options as string[]) || [];

  return (
    <select
      value={String(value ?? "")}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className={inputClasses}
    >
      <option value="">Select...</option>
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  );
}

/**
 * Default Date Input Component
 */
export function DefaultDateInput({
  value,
  onChange,
  disabled,
}: FieldComponentProps) {
  return (
    <input
      type="date"
      value={String(value ?? "")}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className={inputClasses}
    />
  );
}

/**
 * Default DateTime Input Component
 */
export function DefaultDateTimeInput({
  value,
  onChange,
  disabled,
}: FieldComponentProps) {
  return (
    <input
      type="datetime-local"
      value={String(value ?? "")}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className={inputClasses}
    />
  );
}

/**
 * Default JSON Editor Component
 */
export function DefaultJSONEditor({
  value,
  onChange,
  disabled,
}: FieldComponentProps) {
  const stringValue = typeof value === "string"
    ? value
    : JSON.stringify(value, null, 2);

  return (
    <textarea
      value={stringValue}
      onChange={(e) => {
        try {
          onChange(JSON.parse(e.target.value));
        } catch {
          // Keep as string if not valid JSON
          onChange(e.target.value);
        }
      }}
      disabled={disabled}
      rows={6}
      className={`${inputClasses} font-mono text-sm`}
      placeholder="{}"
    />
  );
}

// Non-component exports moved to src/registry/defaultComponents.ts
