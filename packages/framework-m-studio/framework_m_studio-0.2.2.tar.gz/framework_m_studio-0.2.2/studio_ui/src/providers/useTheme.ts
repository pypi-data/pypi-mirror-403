/**
 * useTheme Hook
 *
 * Hook to access the theme context
 */

import { useContext } from "react";
import { ThemeContext } from "./ThemeContext.ts";

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
