/**
 * Breadcrumb Component
 * 
 * Clean minimal breadcrumb navigation
 * Theme-aware
 */

import { useBreadcrumb } from "@refinedev/core";
import { Link } from "react-router";
import { useTheme } from "../../providers/theme";

export const Breadcrumb = () => {
  const { breadcrumbs } = useBreadcrumb();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  return (
    <nav className="flex items-center gap-2 text-sm">
      {breadcrumbs.map((breadcrumb, index) => (
        <div key={`breadcrumb-${breadcrumb.label}`} className="flex items-center gap-2">
          {index > 0 && (
            <svg className={`w-4 h-4 ${isDark ? "text-zinc-600" : "text-gray-400"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          )}
          {breadcrumb.href ? (
            <Link
              to={breadcrumb.href}
              className={`transition-colors ${
                isDark 
                  ? "text-zinc-400 hover:text-white" 
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              {breadcrumb.label}
            </Link>
          ) : (
            <span className={`font-medium ${isDark ? "text-white" : "text-gray-900"}`}>
              {breadcrumb.label}
            </span>
          )}
        </div>
      ))}
    </nav>
  );
};
