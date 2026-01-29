/**
 * AutoTable Component
 * 
 * Auto-generates a table from DocType schema.
 * Used in Sandbox mode for testing list views.
 */

import { useState, useCallback, useMemo } from "react";
import type { FieldData } from "./FieldEditor";

interface AutoTableProps {
  /** Field definitions from DocType schema */
  fields: FieldData[];
  /** Table data */
  data: Record<string, unknown>[];
  /** Callback when row is clicked */
  onRowClick?: (row: Record<string, unknown>, index: number) => void;
  /** Callback when row is deleted */
  onDelete?: (row: Record<string, unknown>, index: number) => void;
  /** Page size for pagination */
  pageSize?: number;
  /** Show pagination */
  paginated?: boolean;
}

/**
 * Format a value for display based on its type
 */
function formatValue(value: unknown, fieldType: string): string {
  if (value === null || value === undefined) {
    return "-";
  }

  switch (fieldType) {
    case "bool":
      return value ? "Yes" : "No";
    case "date":
    case "datetime":
      return String(value);
    case "dict":
    case "json":
    case "list":
      return JSON.stringify(value).slice(0, 50) + "...";
    default:
      return String(value);
  }
}

export function AutoTable({
  fields,
  data,
  onRowClick,
  onDelete,
  pageSize = 10,
  paginated = true,
}: AutoTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  // Limit columns to first 5 fields for display
  const displayFields = useMemo(() => fields.slice(0, 5), [fields]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortField) return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison = String(aVal).localeCompare(String(bVal));
      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [data, sortField, sortDirection]);

  // Paginate data
  const paginatedData = useMemo(() => {
    if (!paginated) return sortedData;
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize, paginated]);

  const totalPages = Math.ceil(data.length / pageSize);

  // Handle column header click for sorting
  const handleSort = useCallback((fieldName: string) => {
    if (sortField === fieldName) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(fieldName);
      setSortDirection("asc");
    }
  }, [sortField]);

  // Handle row click
  const handleRowClick = useCallback(
    (row: Record<string, unknown>, index: number) => {
      onRowClick?.(row, (currentPage - 1) * pageSize + index);
    },
    [onRowClick, currentPage, pageSize]
  );

  // Handle delete
  const handleDelete = useCallback(
    (row: Record<string, unknown>, index: number, e: React.MouseEvent) => {
      e.stopPropagation();
      onDelete?.(row, (currentPage - 1) * pageSize + index);
    },
    [onDelete, currentPage, pageSize]
  );

  return (
    <div className="border border-gray-200 dark:border-zinc-700 rounded-lg overflow-hidden">
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          {/* Header */}
          <thead className="bg-gray-50 dark:bg-zinc-800">
            <tr>
              <th className="w-12 px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-zinc-400">
                #
              </th>
              {displayFields.map((field) => (
                <th
                  key={field.name}
                  onClick={() => handleSort(field.name)}
                  className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-zinc-400 cursor-pointer hover:bg-gray-100 dark:hover:bg-zinc-700 transition-colors"
                >
                  <div className="flex items-center gap-1">
                    {field.name}
                    {sortField === field.name && (
                      <svg
                        className={`w-3 h-3 transition-transform ${
                          sortDirection === "desc" ? "rotate-180" : ""
                        }`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 15l7-7 7 7"
                        />
                      </svg>
                    )}
                  </div>
                </th>
              ))}
              {onDelete && (
                <th className="w-16 px-3 py-2 text-center text-xs font-medium text-gray-500 dark:text-zinc-400">
                  Actions
                </th>
              )}
            </tr>
          </thead>

          {/* Body */}
          <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
            {paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={displayFields.length + 2}
                  className="px-4 py-8 text-center text-gray-400 dark:text-zinc-500 text-sm"
                >
                  No data available.
                </td>
              </tr>
            ) : (
              paginatedData.map((row, index) => (
                <tr
                  key={String(row.id || index)}
                  onClick={() => handleRowClick(row, index)}
                  className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 cursor-pointer transition-colors"
                >
                  <td className="px-3 py-2 text-xs text-gray-400 dark:text-zinc-500">
                    {(currentPage - 1) * pageSize + index + 1}
                  </td>
                  {displayFields.map((field) => (
                    <td
                      key={field.name}
                      className="px-3 py-2 text-sm text-gray-900 dark:text-white truncate max-w-[200px]"
                    >
                      {formatValue(row[field.name], field.type)}
                    </td>
                  ))}
                  {onDelete && (
                    <td className="px-3 py-2 text-center">
                      <button
                        type="button"
                        onClick={(e) => handleDelete(row, index, e)}
                        className="p-1 text-gray-400 hover:text-red-500 dark:text-zinc-500 dark:hover:text-red-400 transition-colors"
                        title="Delete"
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
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {paginated && totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800">
          <div className="text-sm text-gray-500 dark:text-zinc-400">
            Showing {(currentPage - 1) * pageSize + 1} to{" "}
            {Math.min(currentPage * pageSize, data.length)} of {data.length} rows
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm border border-gray-300 dark:border-zinc-600 rounded hover:bg-gray-100 dark:hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600 dark:text-zinc-400">
              Page {currentPage} of {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-sm border border-gray-300 dark:border-zinc-600 rounded hover:bg-gray-100 dark:hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default AutoTable;
