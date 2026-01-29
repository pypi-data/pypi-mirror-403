/**
 * Field Editor Component (RJSF Schema-Driven)
 *
 * Uses React JSON Schema Form (RJSF) to render field property forms
 * based on a JSON Schema definition. Provides custom Tailwind-styled widgets.
 *
 * Field types are fetched from the API and passed as a prop for dynamic loading.
 */

import Form from "@rjsf/core";
import validator from "@rjsf/validator-ajv8";
import {
  RegistryWidgetsType,
  WidgetProps,
  RJSFSchema,
  UiSchema,
  FieldTemplateProps,
  ObjectFieldTemplateProps,
} from "@rjsf/utils";
import { useState, useMemo } from "react";

/**
 * Field type info from the API (/studio/api/field-types)
 */
export interface FieldTypeInfo {
  name: string;
  pydantic_type: string;
  label: string;
  ui_widget: string;
  sqlalchemy_type?: string | null;
  description?: string | null;
}

/**
 * Build the JSON Schema for field properties dynamically based on available types.
 */
function buildFieldSchema(fieldTypes: FieldTypeInfo[]): RJSFSchema {
  return {
    type: "object",
    required: ["name", "type"],
    properties: {
      name: {
        type: "string",
        title: "Field Name",
        description: "Python-valid identifier (e.g., 'user_name')",
        pattern: "^[a-z_][a-z0-9_]*$",
      },
      type: {
        type: "string",
        title: "Type",
        enum: fieldTypes.map(t => t.name),
      },
      required: {
        type: "boolean",
        title: "Required",
        default: true,
      },
      label: {
        type: "string",
        title: "Label",
        description: "Display label (defaults to field name if empty)",
      },
      default: {
        type: "string",
        title: "Default Value",
        description: "Python expression (e.g., '\"hello\"', 'None', '42')",
      },
      description: {
        type: "string",
        title: "Description",
        description: "Docstring for the field",
      },
      // Display options
      hidden: {
        type: "boolean",
        title: "Hidden",
        description: "Hide this field from forms",
        default: false,
      },
      read_only: {
        type: "boolean",
        title: "Read Only",
        description: "Make this field non-editable",
        default: false,
      },
      // Advanced validators
      validators: {
        type: "object",
        title: "Validators",
        properties: {
          min_length: {
            type: "integer",
            title: "Min Length",
            minimum: 0,
          },
          max_length: {
            type: "integer",
            title: "Max Length",
            minimum: 1,
          },
          pattern: {
            type: "string",
            title: "Regex Pattern",
          },
          min_value: {
            type: "number",
            title: "Minimum Value",
          },
          max_value: {
            type: "number",
            title: "Maximum Value",
          },
        },
      },
    },
  };
}

/**
 * Build the UI Schema for form layout dynamically based on available types.
 */
function buildUiSchema(fieldTypes: FieldTypeInfo[]): UiSchema {
  return {
    name: {
      "ui:autofocus": true,
      "ui:placeholder": "field_name",
    },
    type: {
      "ui:widget": "select",
      "ui:enumNames": fieldTypes.map(t => t.label),
    },
    description: {
      "ui:widget": "textarea",
      "ui:options": { rows: 2 },
    },
    validators: {
      "ui:collapsed": true,
    },
  };
}
// Custom Tailwind-styled widgets with theme support
const inputClasses =
  "w-full px-3 py-2 rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 bg-white dark:bg-zinc-800 border-gray-200 dark:border-zinc-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500";

const selectClasses =
  "w-full px-3 py-2 rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 bg-white dark:bg-zinc-800 border-gray-200 dark:border-zinc-700 text-gray-900 dark:text-white";

function TextWidget(props: WidgetProps) {
  const { id, value, required, disabled, onChange, placeholder } = props;
  return (
    <input
      id={id}
      type="text"
      value={value || ""}
      required={required}
      disabled={disabled}
      placeholder={placeholder}
      onChange={e => onChange(e.target.value)}
      className={inputClasses}
    />
  );
}

function TextareaWidget(props: WidgetProps) {
  const { id, value, required, disabled, onChange, options } = props;
  return (
    <textarea
      id={id}
      value={value || ""}
      required={required}
      disabled={disabled}
      rows={(options?.rows as number) || 3}
      onChange={e => onChange(e.target.value)}
      className={`${inputClasses} resize-none`}
    />
  );
}

function SelectWidget(props: WidgetProps) {
  const { id, value, required, disabled, onChange, options } = props;
  const { enumOptions } = options;
  return (
    <select
      id={id}
      value={value || ""}
      required={required}
      disabled={disabled}
      onChange={e => onChange(e.target.value)}
      className={selectClasses}
    >
      <option value="" disabled>
        Select...
      </option>
      {(enumOptions || []).map((opt: { value: string; label: string }) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

function CheckboxWidget(props: WidgetProps) {
  const { id, value, disabled, onChange, label } = props;
  return (
    <div className="flex items-center gap-2">
      <input
        id={id}
        type="checkbox"
        checked={value || false}
        disabled={disabled}
        onChange={e => onChange(e.target.checked)}
        className="w-4 h-4 rounded border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 text-blue-500 focus:ring-blue-500"
      />
      <label htmlFor={id} className="text-sm text-gray-700 dark:text-zinc-300">
        {label}
      </label>
    </div>
  );
}

const customWidgets: RegistryWidgetsType = {
  TextWidget,
  TextareaWidget,
  SelectWidget,
  CheckboxWidget,
};

// Custom field template for better styling
function FieldTemplate(props: FieldTemplateProps) {
  const { id, label, children, errors, description, required } = props;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const hasError = errors && (errors.props as any)?.errors?.length > 0;

  return (
    <div className="mb-4">
      {label && (
        <label
          htmlFor={id}
          className={`block text-sm font-medium mb-1 ${
            hasError ? "text-red-500" : "text-gray-600 dark:text-zinc-400"
          }`}
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      {children}
      {description && (
        <p className="mt-1 text-xs text-gray-500 dark:text-zinc-500">
          {description}
        </p>
      )}
      {hasError && <div className="mt-1 text-xs text-red-500">{errors}</div>}
    </div>
  );
}

// Custom object field template with collapsible sections
function ObjectFieldTemplate(props: ObjectFieldTemplateProps) {
  const { title, properties, uiSchema } = props;
  const [collapsed, setCollapsed] = useState(
    uiSchema?.["ui:collapsed"] || false,
  );

  const isCollapsible = uiSchema?.["ui:collapsed"] !== undefined;

  if (isCollapsible) {
    return (
      <div className="border border-gray-200 dark:border-zinc-700 rounded-lg overflow-hidden mt-4">
        <button
          type="button"
          onClick={() => setCollapsed(!collapsed)}
          className="w-full px-4 py-2 bg-gray-50 dark:bg-zinc-800 text-left text-sm font-medium text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-700 flex items-center justify-between"
        >
          <span>{title || "Advanced"}</span>
          <svg
            className={`w-4 h-4 transition-transform ${collapsed ? "" : "rotate-180"}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
        {!collapsed && (
          <div className="p-4 space-y-2 bg-gray-50/50 dark:bg-zinc-900/50">
            {properties.map(prop => prop.content)}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {title}
        </h3>
      )}
      {properties.map(prop => prop.content)}
    </div>
  );
}

// Field data interface
export interface FieldData {
  name: string;
  type: string;
  required: boolean;
  label?: string;
  default?: string;
  description?: string;
  hidden?: boolean;
  read_only?: boolean;
  validators?: {
    min_length?: number;
    max_length?: number;
    pattern?: string;
    min_value?: number;
    max_value?: number;
  };
}

interface FieldEditorProps {
  field: FieldData | null;
  fieldTypes: FieldTypeInfo[];
  onChange: (field: FieldData) => void;
}

export function FieldEditor({ field, fieldTypes, onChange }: FieldEditorProps) {
  // Build schema dynamically based on available field types
  const fieldSchema = useMemo(() => buildFieldSchema(fieldTypes), [fieldTypes]);
  const uiSchema = useMemo(() => buildUiSchema(fieldTypes), [fieldTypes]);

  if (!field) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500 dark:text-zinc-500">
        <div className="text-center">
          <svg
            className="w-12 h-12 mx-auto mb-3 text-gray-400 dark:text-zinc-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p>Select a field to edit its properties</p>
        </div>
      </div>
    );
  }

  // Generate Python type preview
  const generateTypePreview = () => {
    let type = field.type;
    if (!field.required && !type.includes("None")) {
      type = `${type} | None`;
    }
    let line = `${field.name}: ${type}`;
    if (field.default) {
      line += ` = ${field.default}`;
    }
    return line;
  };

  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Field Properties
      </h3>

      <Form
        schema={fieldSchema}
        uiSchema={uiSchema}
        formData={field}
        validator={validator}
        widgets={customWidgets}
        templates={{
          FieldTemplate,
          ObjectFieldTemplate,
        }}
        onChange={e => onChange(e.formData as FieldData)}
        onSubmit={() => {}} // No submit button
        liveValidate
      >
        {/* Hide submit button */}
        <></>
      </Form>

      {/* Live Type Preview */}
      <div className="mt-6 p-4 bg-gray-100 dark:bg-zinc-900 rounded-lg border border-gray-200 dark:border-zinc-700">
        <div className="text-xs text-gray-500 dark:text-zinc-500 mb-2 flex items-center gap-2">
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
            />
          </svg>
          Generated Python Type
        </div>
        <code className="text-green-600 dark:text-green-400 font-mono text-sm block">
          {generateTypePreview()}
        </code>
        {field.description && (
          <code className="text-gray-500 dark:text-zinc-500 font-mono text-xs block mt-1">
            """docstring: {field.description}"""
          </code>
        )}
      </div>
    </div>
  );
}

export default FieldEditor;
