/**
 * SandboxPreview Component
 *
 * Main preview component for testing DocTypes with mock data.
 * Supports Form view (single record) and Table view (list).
 * Uses in-memory data store for CRUD operations.
 */

import { useState, useCallback, useMemo, useEffect } from "react";
import type { FieldData } from "./FieldEditor";
import { AutoForm } from "./AutoForm";
import { AutoTable } from "./AutoTable";
import {
  generateMockRows,
  generateMockDocument,
} from "../utils/mockDataGenerator";

type ViewMode = "form" | "table";

interface SandboxPreviewProps {
  /** Field definitions from DocType schema */
  fields: FieldData[];
  /** DocType name for display */
  doctypeName: string;
}

export function SandboxPreview({ fields, doctypeName }: SandboxPreviewProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [data, setData] = useState<Record<string, unknown>[]>([]);
  const [selectedRow, setSelectedRow] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  // Generate initial mock data when fields change
  useEffect(() => {
    if (fields.length > 0) {
      setData(generateMockRows(fields, 10));
    }
  }, [fields]);

  // Stats
  const stats = useMemo(
    () => ({
      total: data.length,
      fields: fields.length,
    }),
    [data.length, fields.length]
  );

  // Handle create new record
  const handleCreate = useCallback(() => {
    setSelectedRow(null);
    setSelectedIndex(null);
    setIsCreating(true);
    setShowForm(true);
  }, []);

  // Handle row click for editing
  const handleRowClick = useCallback(
    (row: Record<string, unknown>, index: number) => {
      setSelectedRow(row);
      setSelectedIndex(index);
      setIsCreating(false);
      setShowForm(true);
    },
    []
  );

  // Handle form submit (create or update)
  const handleFormSubmit = useCallback(
    (values: Record<string, unknown>) => {
      if (isCreating) {
        // Create new record with generated ID
        const newRecord = {
          ...values,
          id: crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        setData(prev => [...prev, newRecord]);
      } else if (selectedIndex !== null) {
        // Update existing record
        setData(prev => {
          const updated = [...prev];
          updated[selectedIndex] = {
            ...updated[selectedIndex],
            ...values,
            updated_at: new Date().toISOString(),
          };
          return updated;
        });
      }
      setShowForm(false);
      setSelectedRow(null);
      setSelectedIndex(null);
      setIsCreating(false);
    },
    [isCreating, selectedIndex]
  );

  // Handle delete
  const handleDelete = useCallback(
    (_row: Record<string, unknown>, index: number) => {
      if (confirm(`Delete this ${doctypeName}?`)) {
        setData(prev => prev.filter((_, i) => i !== index));
      }
    },
    [doctypeName]
  );

  // Generate more mock data
  const handleGenerateMore = useCallback(
    (count: number) => {
      setData(prev => [...prev, ...generateMockRows(fields, count)]);
    },
    [fields]
  );

  // Clear all data
  const handleClearData = useCallback(() => {
    if (confirm("Clear all sandbox data?")) {
      setData([]);
    }
  }, []);

  // Close form
  const handleCloseForm = useCallback(() => {
    setShowForm(false);
    setSelectedRow(null);
    setSelectedIndex(null);
    setIsCreating(false);
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-zinc-700">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Sandbox: {doctypeName}
          </h3>
          <span className="text-sm text-gray-500 dark:text-zinc-400">
            {stats.total} records • {stats.fields} fields
          </span>
        </div>

        {/* View Toggles */}
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg overflow-hidden border border-gray-200 dark:border-zinc-700">
            <button
              type="button"
              onClick={() => setViewMode("table")}
              className={`px-3 py-1.5 text-sm transition-colors ${
                viewMode === "table"
                  ? "bg-blue-600 text-white"
                  : "bg-white dark:bg-zinc-800 text-gray-600 dark:text-zinc-400 hover:bg-gray-50 dark:hover:bg-zinc-700"
              }`}
            >
              <span className="flex items-center gap-1.5">
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
                    d="M4 6h16M4 10h16M4 14h16M4 18h16"
                  />
                </svg>
                Table
              </span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("form")}
              className={`px-3 py-1.5 text-sm transition-colors ${
                viewMode === "form"
                  ? "bg-blue-600 text-white"
                  : "bg-white dark:bg-zinc-800 text-gray-600 dark:text-zinc-400 hover:bg-gray-50 dark:hover:bg-zinc-700"
              }`}
            >
              <span className="flex items-center gap-1.5">
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
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                Form
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-100 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-900">
        <button
          type="button"
          onClick={handleCreate}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
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
          New
        </button>
        <div className="flex items-center gap-1 border-l border-gray-200 dark:border-zinc-700 pl-2 ml-1">
          <button
            type="button"
            onClick={() => handleGenerateMore(5)}
            className="px-2 py-1.5 text-xs text-gray-600 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors"
          >
            +5 rows
          </button>
          <button
            type="button"
            onClick={() => handleGenerateMore(50)}
            className="px-2 py-1.5 text-xs text-gray-600 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors"
          >
            +50 rows
          </button>
          <button
            type="button"
            onClick={handleClearData}
            className="px-2 py-1.5 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Main View */}
        <div
          className={`flex-1 overflow-auto p-4 ${
            showForm ? "hidden md:block" : ""
          }`}
        >
          {viewMode === "table" ? (
            <AutoTable
              fields={fields}
              data={data}
              onRowClick={handleRowClick}
              onDelete={handleDelete}
              pageSize={10}
              paginated
            />
          ) : (
            <div className="max-w-xl">
              {data.length > 0 ? (
                <>
                  <div className="mb-4 text-sm text-gray-500 dark:text-zinc-400">
                    Showing record 1 of {data.length}
                  </div>
                  <AutoForm
                    fields={fields}
                    initialValues={data[0]}
                    onSubmit={handleFormSubmit}
                    readOnly
                  />
                </>
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-zinc-500">
                  No records. Click "New" to create one.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Form Sidebar */}
        {showForm && (
          <div className="w-full md:w-96 border-l border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-zinc-700">
              <h4 className="font-medium text-gray-900 dark:text-white">
                {isCreating ? "New Record" : "Edit Record"}
              </h4>
              <button
                type="button"
                onClick={handleCloseForm}
                className="p-1 text-gray-400 hover:text-gray-600 dark:text-zinc-500 dark:hover:text-zinc-300"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <AutoForm
                fields={fields}
                initialValues={
                  isCreating ? generateMockDocument(fields) : selectedRow || {}
                }
                onSubmit={handleFormSubmit}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SandboxPreview;
