/**
 * TableFieldEditor Component
 * 
 * A grid/table component for editing array fields (child tables).
 * Provides CRUD operations for rows and inline editing for simple types.
 * 
 * Level 1: Grid/Table view for child table data
 * Level 2+: Uses NestedEditorDrawer for complex nested editing
 */

import { useState, useCallback } from "react";

/**
 * Column definition for the table
 */
export interface ColumnDef {
  name: string;
  label: string;
  type: string;
  required?: boolean;
}

/**
 * Row data type - generic record
 */
export type RowData = Record<string, unknown>;

interface TableFieldEditorProps {
  /** Array of row data */
  value: RowData[];
  /** Column definitions from child DocType fields */
  columns: ColumnDef[];
  /** Callback when value changes */
  onChange: (value: RowData[]) => void;
  /** Callback when a row is clicked for detailed editing */
  onRowClick?: (row: RowData, index: number) => void;
  /** Whether the table is read-only */
  readOnly?: boolean;
}

/**
 * Create an empty row with default values based on column types
 */
function createEmptyRow(columns: ColumnDef[]): RowData {
  const row: RowData = {};
  for (const col of columns) {
    switch (col.type) {
      case "bool":
        row[col.name] = false;
        break;
      case "int":
      case "float":
        row[col.name] = 0;
        break;
      default:
        row[col.name] = "";
    }
  }
  return row;
}

/**
 * Get input type for a column based on its type
 */
function getInputType(type: string): string {
  switch (type) {
    case "int":
    case "float":
    case "Decimal":
      return "number";
    case "bool":
      return "checkbox";
    case "date":
      return "date";
    case "datetime":
      return "datetime-local";
    case "email":
      return "email";
    case "url":
      return "url";
    default:
      return "text";
  }
}

export function TableFieldEditor({
  value = [],
  columns,
  onChange,
  onRowClick,
  readOnly = false,
}: TableFieldEditorProps) {
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  // Add a new row
  const handleAddRow = useCallback(() => {
    const newRow = createEmptyRow(columns);
    onChange([...value, newRow]);
    setSelectedRow(value.length); // Select the new row
  }, [columns, value, onChange]);

  // Delete a row
  const handleDeleteRow = useCallback(
    (index: number, e: React.MouseEvent) => {
      e.stopPropagation(); // Prevent row click
      const newValue = [...value];
      newValue.splice(index, 1);
      onChange(newValue);
      if (selectedRow === index) {
        setSelectedRow(null);
      } else if (selectedRow !== null && selectedRow > index) {
        setSelectedRow(selectedRow - 1);
      }
    },
    [value, onChange, selectedRow]
  );

  // Update a cell value
  const handleCellChange = useCallback(
    (rowIndex: number, colName: string, cellValue: unknown) => {
      const newValue = [...value];
      newValue[rowIndex] = { ...newValue[rowIndex], [colName]: cellValue };
      onChange(newValue);
    },
    [value, onChange]
  );

  // Handle row click
  const handleRowClick = useCallback(
    (row: RowData, index: number) => {
      setSelectedRow(index);
      onRowClick?.(row, index);
    },
    [onRowClick]
  );

  return (
    <div className="border border-gray-200 dark:border-zinc-700 rounded-lg overflow-hidden">
      {/* Table Header */}
      <div className="bg-gray-50 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700">
        <div className="flex">
          {/* Row number column */}
          <div className="w-12 px-3 py-2 text-xs font-medium text-gray-500 dark:text-zinc-400 text-center">
            #
          </div>
          {/* Data columns */}
          {columns.map((col) => (
            <div
              key={col.name}
              className="flex-1 px-3 py-2 text-xs font-medium text-gray-500 dark:text-zinc-400"
            >
              {col.label}
              {col.required && <span className="text-red-500 ml-1">*</span>}
            </div>
          ))}
          {/* Actions column */}
          {!readOnly && (
            <div className="w-16 px-3 py-2 text-xs font-medium text-gray-500 dark:text-zinc-400 text-center">
              Actions
            </div>
          )}
        </div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-gray-100 dark:divide-zinc-800">
        {value.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-400 dark:text-zinc-500 text-sm">
            No rows yet. Click "Add Row" to add data.
          </div>
        ) : (
          value.map((row, rowIndex) => (
            <div
              key={rowIndex}
              className={`flex hover:bg-gray-50 dark:hover:bg-zinc-800/50 cursor-pointer transition-colors ${
                selectedRow === rowIndex
                  ? "bg-blue-50 dark:bg-blue-900/20"
                  : ""
              }`}
              onClick={() => handleRowClick(row, rowIndex)}
            >
              {/* Row number */}
              <div className="w-12 px-3 py-2 text-xs text-gray-400 dark:text-zinc-500 text-center flex items-center justify-center">
                {rowIndex + 1}
              </div>
              {/* Data cells */}
              {columns.map((col) => (
                <div key={col.name} className="flex-1 px-2 py-1">
                  {col.type === "bool" ? (
                    <input
                      type="checkbox"
                      checked={Boolean(row[col.name])}
                      onChange={(e) =>
                        handleCellChange(rowIndex, col.name, e.target.checked)
                      }
                      onClick={(e) => e.stopPropagation()}
                      disabled={readOnly}
                      className="rounded border-gray-300 dark:border-zinc-600 text-blue-600 focus:ring-blue-500"
                    />
                  ) : (
                    <input
                      type={getInputType(col.type)}
                      value={String(row[col.name] ?? "")}
                      onChange={(e) =>
                        handleCellChange(
                          rowIndex,
                          col.name,
                          col.type === "int"
                            ? parseInt(e.target.value) || 0
                            : col.type === "float" || col.type === "Decimal"
                            ? parseFloat(e.target.value) || 0
                            : e.target.value
                        )
                      }
                      onClick={(e) => e.stopPropagation()}
                      disabled={readOnly}
                      className="w-full px-2 py-1 text-sm bg-transparent border border-transparent hover:border-gray-200 dark:hover:border-zinc-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded transition-colors outline-none text-gray-900 dark:text-white"
                    />
                  )}
                </div>
              ))}
              {/* Delete button */}
              {!readOnly && (
                <div className="w-16 px-2 py-1 flex items-center justify-center">
                  <button
                    type="button"
                    onClick={(e) => handleDeleteRow(rowIndex, e)}
                    className="p-1 text-gray-400 hover:text-red-500 dark:text-zinc-500 dark:hover:text-red-400 transition-colors"
                    title="Delete row"
                  >
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
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Add Row Button */}
      {!readOnly && (
        <div className="border-t border-gray-200 dark:border-zinc-700 p-2">
          <button
            type="button"
            onClick={handleAddRow}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
          >
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
                d="M12 4v16m8-8H4"
              />
            </svg>
            Add Row
          </button>
        </div>
      )}
    </div>
  );
}

export default TableFieldEditor;
