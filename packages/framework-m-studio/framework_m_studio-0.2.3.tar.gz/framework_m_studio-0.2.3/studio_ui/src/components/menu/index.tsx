/**
 * Menu Component
 * 
 * Sidebar navigation with icons and hover states
 * Theme-aware
 */

import { useMenu } from "@refinedev/core";
import { NavLink } from "react-router";
import { useTheme } from "../../providers/theme";

// Icon components
const DocTypeIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const getIcon = (label: string) => {
  switch (label?.toLowerCase()) {
    case "doctypes":
      return <DocTypeIcon />;
    default:
      return <DocTypeIcon />;
  }
};

export const Menu = () => {
  const { menuItems } = useMenu();
  const { theme } = useTheme();
  const isDark = theme === "dark";

  return (
    <nav className="py-4 px-3">
      <div className="space-y-1">
        {menuItems.map((item) => (
          <NavLink
            key={item.key}
            to={item.route ?? "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-blue-500/10 text-blue-500"
                  : isDark 
                    ? "text-zinc-400 hover:text-white hover:bg-zinc-800" 
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              }`
            }
          >
            {getIcon(String(item.label ?? ""))}
            <span>{item.label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
};
