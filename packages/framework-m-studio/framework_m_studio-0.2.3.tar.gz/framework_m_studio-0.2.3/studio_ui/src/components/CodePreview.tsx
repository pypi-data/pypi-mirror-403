/**
 * Code Preview Component (Monaco Editor)
 *
 * Displays generated Python code for a DocType schema using Monaco Editor.
 * Features:
 * - Python syntax highlighting
 * - Read-only mode
 * - Dark theme
 * - Auto-update on schema change
 */

import Editor from "@monaco-editor/react";
import { useMemo } from "react";
import { FieldData } from "./FieldEditor";

interface DocTypeSchema {
  name: string;
  docstring?: string;
  fields: FieldData[];
}

interface CodePreviewProps {
  schema: DocTypeSchema;
  className?: string;
}

/**
 * Generate Python code from DocType schema
 */
function generatePythonCode(schema: DocTypeSchema): string {
  const lines: string[] = [];

  // Check if we need Annotated and Field imports
  const needsAnnotated = schema.fields.some(
    f => f.validators && Object.keys(f.validators).length > 0,
  );

  // Imports
  lines.push('"""');
  lines.push(`${schema.name} DocType`);
  if (schema.docstring) {
    lines.push("");
    lines.push(schema.docstring);
  }
  lines.push('"""');
  lines.push("");
  lines.push("from __future__ import annotations");
  lines.push("");

  // Collect needed imports
  const typeImports = new Set<string>();
  const dateTimeNeeded = schema.fields.some(
    f => f.type === "datetime" || f.type === "date",
  );
  const uuidNeeded = schema.fields.some(f => f.type === "UUID");
  const decimalNeeded = schema.fields.some(f => f.type === "Decimal");

  if (needsAnnotated) {
    typeImports.add("from typing import Annotated");
    typeImports.add("");
    typeImports.add("from pydantic import Field");
  }

  if (dateTimeNeeded) {
    typeImports.add("from datetime import datetime, date");
  }
  if (uuidNeeded) {
    typeImports.add("from uuid import UUID");
  }
  if (decimalNeeded) {
    typeImports.add("from decimal import Decimal");
  }

  typeImports.forEach(imp => lines.push(imp));
  if (typeImports.size > 0) lines.push("");

  lines.push("from framework_m.core.base import BaseDocType");
  lines.push("");
  lines.push("");

  // Class definition
  lines.push(`class ${schema.name}(BaseDocType):`);

  // Docstring
  if (schema.docstring) {
    lines.push(`    """${schema.docstring}"""`);
    lines.push("");
  }

  // Fields
  if (schema.fields.length === 0) {
    lines.push("    pass");
  } else {
    schema.fields.forEach(field => {
      // Strip existing Annotated wrapper if present
      let fieldType = field.type;
      const annotatedMatch = fieldType.match(/^Annotated\[(.*?)\s*,.*\]$/s);
      if (annotatedMatch) {
        fieldType = annotatedMatch[1].trim();
      }

      // Build Field() arguments for validators, description, and label
      const fieldArgs: string[] = [];
      if (field.validators) {
        const v = field.validators;
        if (v.min_length !== undefined && v.min_length !== null) {
          fieldArgs.push(`min_length=${v.min_length}`);
        }
        if (v.max_length !== undefined && v.max_length !== null) {
          fieldArgs.push(`max_length=${v.max_length}`);
        }
        if (v.pattern) {
          fieldArgs.push(`pattern="${v.pattern}"`);
        }
        if (v.min_value !== undefined && v.min_value !== null) {
          fieldArgs.push(`ge=${v.min_value}`);
        }
        if (v.max_value !== undefined && v.max_value !== null) {
          fieldArgs.push(`le=${v.max_value}`);
        }
      }

      // Add description if present
      if (field.description) {
        fieldArgs.push(`description="${field.description}"`);
      }

      // Add label if present
      if (field.label) {
        fieldArgs.push(`label="${field.label}"`);
      }

      // Handle type annotation with validators
      if (fieldArgs.length > 0) {
        const fieldDef = `Field(${fieldArgs.join(", ")})`;
        if (!field.required && !fieldType.includes("None")) {
          fieldType = `Annotated[${fieldType} | None, ${fieldDef}]`;
        } else {
          fieldType = `Annotated[${fieldType}, ${fieldDef}]`;
        }

        // Build field line
        let line = `    ${field.name}: ${fieldType}`;

        // Add default value
        if (field.default) {
          line += ` = ${field.default}`;
        } else if (!field.required) {
          line += " = None";
        }

        lines.push(line);
      } else {
        // No validators, simple field
        // Handle optional fields
        if (!field.required && !fieldType.includes("None")) {
          fieldType = `${fieldType} | None`;
        }

        // Build field line
        let line = `    ${field.name}: ${fieldType}`;

        // Add default value
        if (field.default) {
          line += ` = ${field.default}`;
        } else if (!field.required) {
          line += " = None";
        }

        lines.push(line);
      }
    });
  }

  lines.push("");

  // Add Config class stub
  lines.push("    class Config:");
  lines.push(`        tablename = "${toSnakeCase(schema.name)}"`);
  lines.push(`        verbose_name = "${schema.name}"`);
  lines.push("");

  return lines.join("\n");
}

/**
 * Convert PascalCase to snake_case
 */
function toSnakeCase(name: string): string {
  return name
    .replace(/([A-Z])/g, "_$1")
    .toLowerCase()
    .replace(/^_/, "");
}

export function CodePreview({ schema, className = "" }: CodePreviewProps) {
  // Memoize code generation
  const code = useMemo(() => generatePythonCode(schema), [schema]);

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <svg
            className="w-4 h-4 text-blue-400"
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
          <span className="text-sm font-medium text-slate-300">
            {toSnakeCase(schema.name || "doctype")}.py
          </span>
        </div>
        <button
          onClick={() => navigator.clipboard.writeText(code)}
          className="text-xs text-slate-400 hover:text-white transition-colors flex items-center gap-1"
        >
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          Copy
        </button>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 min-h-0">
        <Editor
          height="100%"
          language="python"
          value={code}
          theme="vs-dark"
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true,
            folding: true,
            wordWrap: "on",
            padding: { top: 12, bottom: 12 },
            renderLineHighlight: "none",
            overviewRulerBorder: false,
            hideCursorInOverviewRuler: true,
            scrollbar: {
              vertical: "auto",
              horizontal: "hidden",
              useShadows: false,
            },
          }}
        />
      </div>
    </div>
  );
}

export default CodePreview;
