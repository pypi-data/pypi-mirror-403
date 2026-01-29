/**
 * NestedEditorDrawer Component
 * 
 * A slide-in drawer for editing nested/complex records.
 * Used for Level 2+ drill-down pattern when editing nested child tables.
 * 
 * Features:
 * - Slides in from the right
 * - Breadcrumb navigation for context
 * - Supports infinite nesting
 */

import { useEffect, useCallback } from "react";

interface NestedEditorDrawerProps {
  /** Whether the drawer is open */
  isOpen: boolean;
  /** Callback to close the drawer */
  onClose: () => void;
  /** Title for the drawer */
  title: string;
  /** Breadcrumb navigation items */
  breadcrumb?: string[];
  /** Content to render inside the drawer */
  children: React.ReactNode;
  /** Width of the drawer (default: w-96) */
  width?: string;
}

export function NestedEditorDrawer({
  isOpen,
  onClose,
  title,
  breadcrumb = [],
  children,
  width = "w-[500px]",
}: NestedEditorDrawerProps) {
  // Close on escape key
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      // Prevent body scroll when drawer is open
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) {
    return null;
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/30 dark:bg-black/50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 h-full ${width} bg-white dark:bg-zinc-900 shadow-xl z-50 transform transition-transform duration-300 ease-in-out flex flex-col`}
        style={{ transform: isOpen ? "translateX(0)" : "translateX(100%)" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-zinc-700">
          <div className="flex-1 min-w-0">
            {/* Breadcrumb */}
            {breadcrumb.length > 0 && (
              <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-zinc-400 mb-1">
                {breadcrumb.map((item, index) => (
                  <span key={index} className="flex items-center gap-1">
                    {index > 0 && (
                      <svg
                        className="w-3 h-3"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    )}
                    <span className="truncate">{item}</span>
                  </span>
                ))}
              </div>
            )}
            {/* Title */}
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {title}
            </h2>
          </div>

          {/* Close button */}
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 dark:text-zinc-500 dark:hover:text-zinc-300 transition-colors ml-2"
            title="Close (Esc)"
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

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">{children}</div>

        {/* Footer with back button */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-zinc-700">
          <button
            type="button"
            onClick={onClose}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors"
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
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Back
          </button>
        </div>
      </div>
    </>
  );
}

export default NestedEditorDrawer;
