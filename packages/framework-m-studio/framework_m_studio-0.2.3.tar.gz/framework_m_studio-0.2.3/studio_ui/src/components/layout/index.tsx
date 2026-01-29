/**
 * Layout Component
 * 
 * Professional minimal layout with:
 * - Fixed sidebar navigation
 * - Header with breadcrumb and theme toggle
 * - Scrollable content area
 */

import type { PropsWithChildren } from "react";
import { Breadcrumb } from "../breadcrumb";
import { Menu } from "../menu";
import { useTheme } from "../../providers/theme";

export const Layout: React.FC<PropsWithChildren> = ({ children }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className={`flex h-screen ${theme === "dark" ? "bg-[#0a0a0b]" : "bg-gray-50"}`}>
      {/* Sidebar */}
      <aside className={`w-56 flex-shrink-0 border-r ${
        theme === "dark" 
          ? "bg-[#111113] border-[#27272a]" 
          : "bg-white border-gray-200"
      }`}>
        <div className={`flex items-center h-14 px-4 border-b ${
          theme === "dark" ? "border-[#27272a]" : "border-gray-200"
        }`}>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">M</span>
            </div>
            <span className={`font-semibold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              Studio
            </span>
          </div>
        </div>
        <Menu />
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {/* Header */}
        <header className={`h-14 flex-shrink-0 flex items-center justify-between px-6 border-b ${
          theme === "dark" 
            ? "bg-[#111113] border-[#27272a]" 
            : "bg-white border-gray-200"
        }`}>
          <Breadcrumb />
          
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-lg transition-colors ${
              theme === "dark"
                ? "text-[#a1a1aa] hover:text-white hover:bg-[#27272a]"
                : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"
            }`}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {children}
        </div>
      </main>
    </div>
  );
};
