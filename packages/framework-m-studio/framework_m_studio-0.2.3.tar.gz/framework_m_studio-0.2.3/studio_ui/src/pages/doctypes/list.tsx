/**
 * DocType List Page
 *
 * Professional data table with search, sorting, and actions
 * Theme-aware: supports light and dark modes
 */

import { useList, useGo, useDelete } from "@refinedev/core";
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
} from "@tanstack/react-table";
import { useState, useMemo, useCallback } from "react";
import { useTheme } from "../../providers/theme";

interface DocTypeRecord {
  name: string;
  module: string;
  fields: { name: string; type: string }[];
  docstring?: string;
}

const columnHelper = createColumnHelper<DocTypeRecord>();

export function DocTypeList() {
  const go = useGo();
  const { theme } = useTheme();
  const [globalFilter, setGlobalFilter] = useState("");
  const isDark = theme === "dark";

  // Fetch data
  const { result, query } = useList<DocTypeRecord>({
    resource: "doctypes",
  });

  // Delete mutation
  const deleteMutation = useDelete();

  const handleDelete = useCallback(
    async (name: string) => {
      try {
        await deleteMutation.mutateAsync({
          resource: "doctypes",
          id: name,
        });
        // Refetch list after delete
        query.refetch();
      } catch {
        alert("Failed to delete DocType");
      }
    },
    [deleteMutation, query]
  );

  const data = useMemo(() => result?.data ?? [], [result?.data]);

  // Table columns
  const columns = useMemo(
    () => [
      columnHelper.accessor("name", {
        header: "Name",
        cell: info => (
          <span
            className={`font-medium ${isDark ? "text-white" : "text-gray-900"}`}
          >
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor("module", {
        header: "Module",
        cell: info => (
          <span
            className={`font-mono text-xs ${isDark ? "text-zinc-500" : "text-gray-500"
              }`}
          >
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor(row => row.fields?.length ?? 0, {
        id: "fields",
        header: "Fields",
        cell: info => (
          <span
            className={`inline-flex items-center justify-center w-8 h-6 rounded text-xs ${isDark ? "bg-zinc-800 text-zinc-400" : "bg-gray-100 text-gray-600"
              }`}
          >
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor("docstring", {
        header: "Description",
        cell: info => {
          const value = info.getValue();
          if (!value)
            return (
              <span className={isDark ? "text-zinc-600" : "text-gray-400"}>
                —
              </span>
            );
          return (
            <span
              className={`line-clamp-2 text-sm ${isDark ? "text-zinc-400" : "text-gray-600"
                }`}
            >
              {value.slice(0, 100)}
              {value.length > 100 && "..."}
            </span>
          );
        },
      }),
      columnHelper.display({
        id: "actions",
        header: "",
        cell: info => (
          <div className="flex items-center gap-2">
            <button
              onClick={e => {
                e.stopPropagation();
                go({ to: `/doctypes/edit/${info.row.original.name}` });
              }}
              className="px-3 py-1.5 text-xs font-medium text-blue-500 hover:text-blue-600 hover:bg-blue-500/10 rounded transition-colors"
            >
              Edit
            </button>
            <button
              onClick={async e => {
                e.stopPropagation();
                const confirmed = window.confirm(
                  `Delete DocType "${info.row.original.name}"? This will delete the Python file.`
                );
                if (confirmed) {
                  await handleDelete(info.row.original.name);
                }
              }}
              className="px-3 py-1.5 text-xs font-medium text-red-500 hover:text-red-600 hover:bg-red-500/10 rounded transition-colors"
            >
              Delete
            </button>
          </div>
        ),
      }),
    ],
    [go, isDark, handleDelete]
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    state: {
      globalFilter,
    },
    onGlobalFilterChange: setGlobalFilter,
  });

  if (query.isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div
          className={`flex items-center gap-3 ${isDark ? "text-zinc-400" : "text-gray-500"
            }`}
        >
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span>Loading DocTypes...</span>
        </div>
      </div>
    );
  }

  if (query.isError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-red-500/10 flex items-center justify-center">
            <svg
              className="w-6 h-6 text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <p className="text-red-400 font-medium">Failed to load DocTypes</p>
          <p
            className={`text-sm mt-1 ${isDark ? "text-zinc-500" : "text-gray-500"
              }`}
          >
            Make sure the Studio API is running
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex-1 min-w-0">
          <h1
            className={`text-2xl font-semibold ${isDark ? "text-white" : "text-gray-900"
              }`}
          >
            DocTypes
          </h1>
          <p
            className={`text-sm mt-1 ${isDark ? "text-zinc-400" : "text-gray-500"
              }`}
          >
            {data.length} DocType{data.length !== 1 ? "s" : ""} in your project
          </p>
        </div>
        <button
          onClick={() => go({ to: "/doctypes/create" })}
          className="flex-shrink-0 flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white text-base font-medium rounded-lg transition-colors shadow-sm whitespace-nowrap"
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
              d="M12 4v16m8-8H4"
            />
          </svg>
          New DocType
        </button>
      </div>

      {/* Search Bar */}
      <div className="mb-6 mt-4">
        <div
          className={`flex h-12 w-full items-center gap-3 rounded-lg px-4
      outline-none transition-all ring-1
      ${isDark
              ? "bg-zinc-800/50 ring-zinc-800/50 focus-within:ring-blue-500/50 text-white"
              : "bg-white ring-gray-200 focus-within:ring-blue-500/50 text-gray-900 shadow-sm"
            }`}
        >
          {/* Icon */}
          <svg
            className={`h-5 w-5 flex-shrink-0 ${isDark ? "text-zinc-500" : "text-gray-400"
              }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>

          {/* Input */}
          <input
            type="text"
            placeholder="Search DocTypes..."
            value={globalFilter}
            onChange={e => setGlobalFilter(e.target.value)}
            className={`search-input h-full w-full bg-transparent text-base
        placeholder:${isDark ? "text-zinc-500" : "text-gray-500"}
        border-0 outline-none focus:outline-none focus-visible:outline-none
        focus:border-transparent focus-visible:border-transparent
        focus:ring-0 focus:ring-offset-0
        focus-visible:ring-0 focus-visible:ring-offset-0
        appearance-none`}
          />
        </div>
      </div>

      {/* Table Container */}
      <div
        className={`rounded-xl overflow-hidden shadow-sm ring-1 ${isDark
          ? "bg-zinc-900/50 ring-zinc-800/50"
          : "bg-white ring-gray-200"
          }`}
      >
        <table className="w-full border-collapse">
          <thead>
            <tr
              className={`border-b transition-colors ${isDark ? "bg-zinc-800/30 border-zinc-800/50" : "bg-gray-50 border-gray-200/50"
                }`}
            >
              {table.getHeaderGroups().map(headerGroup =>
                headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    className={`px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider ${isDark ? "text-zinc-500" : "text-gray-600"
                      }`}
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                  </th>
                ))
              )}
            </tr>
          </thead>
          <tbody
            className={`divide-y ${isDark ? "divide-zinc-800/50" : "divide-gray-200/50"
              }`}
          >
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td
                  colSpan={5}
                  className={`px-4 py-12 text-center ${isDark ? "text-zinc-500" : "text-gray-500"
                    }`}
                >
                  {globalFilter
                    ? "No matching DocTypes found"
                    : "No DocTypes yet"}
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map(row => (
                <tr
                  key={row.id}
                  onClick={() =>
                    go({ to: `/doctypes/edit/${row.original.name}` })
                  }
                  className={`cursor-pointer transition-colors ${isDark ? "hover:bg-zinc-800/50" : "hover:bg-gray-50"
                    }`}
                >
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-6 py-3">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DocTypeList;
