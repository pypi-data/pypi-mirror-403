/**
 * AutoForm Component
 * 
 * Auto-generates a form from DocType schema.
 * Used in Sandbox mode for testing form data entry.
 */

import { useState, useCallback } from "react";
import type { FieldData } from "./FieldEditor";
import { resolveFieldComponent } from "./fields/resolveFieldComponent.ts";
import type { FieldComponentProps } from "../registry/fieldComponents";

interface AutoFormProps {
  /** Field definitions from DocType schema */
  fields: FieldData[];
  /** Initial values for the form */
  initialValues?: Record<string, unknown>;
  /** Callback when form is submitted */
  onSubmit?: (values: Record<string, unknown>) => void;
  /** Callback when values change */
  onChange?: (values: Record<string, unknown>) => void;
  /** Whether the form is read-only */
  readOnly?: boolean;
}

interface ValidationError {
  field: string;
  message: string;
}

/**
 * Map field type to ui_widget for component resolution
 */
function getUiWidget(fieldType: string): string {
  const typeToWidget: Record<string, string> = {
    str: "text",
    text: "textarea",
    int: "number",
    float: "number",
    Decimal: "number",
    bool: "checkbox",
    date: "date",
    datetime: "datetime",
    email: "email",
    url: "url",
    dict: "json",
    json: "json",
    list: "json",
  };
  return typeToWidget[fieldType] || "text";
}

export function AutoForm({
  fields,
  initialValues = {},
  onSubmit,
  onChange,
  readOnly = false,
}: AutoFormProps) {
  const [values, setValues] = useState<Record<string, unknown>>(initialValues);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [submitted, setSubmitted] = useState(false);

  // Validate form
  const validate = useCallback((): ValidationError[] => {
    const newErrors: ValidationError[] = [];

    for (const field of fields) {
      const value = values[field.name];

      // Required field validation
      if (field.required) {
        if (value === undefined || value === null || value === "") {
          newErrors.push({
            field: field.name,
            message: `${field.name} is required`,
          });
        }
      }

      // Validator rules from field.validators
      if (field.validators && value !== undefined && value !== null && value !== "") {
        const { min_length, max_length, min_value, max_value, pattern } = field.validators;

        if (min_length !== undefined && typeof value === "string" && value.length < min_length) {
          newErrors.push({
            field: field.name,
            message: `Minimum length is ${min_length}`,
          });
        }

        if (max_length !== undefined && typeof value === "string" && value.length > max_length) {
          newErrors.push({
            field: field.name,
            message: `Maximum length is ${max_length}`,
          });
        }

        if (min_value !== undefined && typeof value === "number" && value < min_value) {
          newErrors.push({
            field: field.name,
            message: `Minimum value is ${min_value}`,
          });
        }

        if (max_value !== undefined && typeof value === "number" && value > max_value) {
          newErrors.push({
            field: field.name,
            message: `Maximum value is ${max_value}`,
          });
        }

        if (pattern !== undefined && typeof value === "string") {
          try {
            const regex = new RegExp(pattern);
            if (!regex.test(value)) {
              newErrors.push({
                field: field.name,
                message: `Does not match pattern: ${pattern}`,
              });
            }
          } catch {
            // Invalid regex, skip
          }
        }
      }
    }

    return newErrors;
  }, [fields, values]);

  // Handle field change
  const handleFieldChange = useCallback(
    (fieldName: string, value: unknown) => {
      const newValues = { ...values, [fieldName]: value };
      setValues(newValues);
      onChange?.(newValues);

      // Clear error for this field when user starts typing
      if (submitted) {
        setErrors((prev) => prev.filter((e) => e.field !== fieldName));
      }
    },
    [values, onChange, submitted]
  );

  // Handle form submit
  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setSubmitted(true);

      const validationErrors = validate();
      setErrors(validationErrors);

      if (validationErrors.length === 0) {
        onSubmit?.(values);
      }
    },
    [validate, values, onSubmit]
  );

  // Get error for a field
  const getFieldError = (fieldName: string): string | undefined => {
    return errors.find((e) => e.field === fieldName)?.message;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {fields.map((field) => {
        const uiWidget = getUiWidget(field.type);
        const Component = resolveFieldComponent(uiWidget);
        const error = getFieldError(field.name);
        const fieldProps: FieldComponentProps = {
          value: values[field.name],
          onChange: (val) => handleFieldChange(field.name, val),
          fieldName: field.name,
          fieldType: field.type,
          disabled: readOnly,
          required: field.required,
          description: field.description,
          schema: { type: field.type, ...field.validators },
        };

        return (
          <div key={field.name} className="space-y-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300">
              {field.name}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <Component {...fieldProps} />
            {field.description && (
              <p className="text-xs text-gray-500 dark:text-zinc-500">
                {field.description}
              </p>
            )}
            {error && (
              <p className="text-xs text-red-500">{error}</p>
            )}
          </div>
        );
      })}

      {/* Submit button */}
      {!readOnly && onSubmit && (
        <div className="pt-4 border-t border-gray-200 dark:border-zinc-700">
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Submit
          </button>
          {errors.length > 0 && (
            <p className="mt-2 text-sm text-red-500">
              Please fix {errors.length} validation error(s) above.
            </p>
          )}
        </div>
      )}
    </form>
  );
}

export default AutoForm;
