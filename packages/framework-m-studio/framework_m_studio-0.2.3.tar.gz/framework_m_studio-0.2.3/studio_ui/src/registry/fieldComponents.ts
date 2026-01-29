/**
 * Field Component Registry
 * 
 * Allows apps to register custom React components for field types in Studio.
 * Custom components are stored in window.__STUDIO_FIELD_COMPONENTS__ for
 * discovery by the Studio UI.
 * 
 * @example
 * // In your app's frontend/index.ts:
 * import { registerFieldComponent } from '@framework-m/studio';
 * import StarRating from './components/StarRating';
 * 
 * registerFieldComponent('Rating', StarRating);
 */

import { ComponentType } from "react";

/**
 * Props passed to custom field components
 */
export interface FieldComponentProps {
  /** Current field value */
  value: unknown;
  /** Callback to update the value */
  onChange: (value: unknown) => void;
  /** Name of the field */
  fieldName: string;
  /** Type of the field (e.g., 'str', 'int', 'Rating') */
  fieldType: string;
  /** Whether the field is disabled */
  disabled?: boolean;
  /** Whether the field is required */
  required?: boolean;
  /** Field description/placeholder */
  description?: string;
  /** Additional props from field schema */
  schema?: Record<string, unknown>;
}

// Extend Window interface for TypeScript
declare global {
  interface Window {
    __STUDIO_FIELD_COMPONENTS__?: Map<string, ComponentType<FieldComponentProps>>;
  }
}

/**
 * Get or create the global component registry
 */
function getRegistry(): Map<string, ComponentType<FieldComponentProps>> {
  if (!window.__STUDIO_FIELD_COMPONENTS__) {
    window.__STUDIO_FIELD_COMPONENTS__ = new Map();
  }
  return window.__STUDIO_FIELD_COMPONENTS__;
}

/**
 * Register a custom field component for a field type.
 * 
 * @param name - The field type name (matches ui_widget from FieldRegistry)
 * @param component - React component to render for this field type
 * 
 * @example
 * registerFieldComponent('Rating', StarRatingComponent);
 * registerFieldComponent('ColorPicker', ColorPickerComponent);
 */
export function registerFieldComponent(
  name: string,
  component: ComponentType<FieldComponentProps>
): void {
  const registry = getRegistry();
  
  if (registry.has(name)) {
    console.warn(`[Studio] Overwriting existing field component: ${name}`);
  }
  
  registry.set(name, component);
  console.log(`[Studio] Registered field component: ${name}`);
}

/**
 * Get a custom field component by name.
 * 
 * @param name - The field type name to look up
 * @returns The registered component, or null if not found
 * 
 * @example
 * const RatingComponent = getFieldComponent('Rating');
 * if (RatingComponent) {
 *   return <RatingComponent value={value} onChange={onChange} {...props} />;
 * }
 */
export function getFieldComponent(
  name: string
): ComponentType<FieldComponentProps> | null {
  const registry = getRegistry();
  return registry.get(name) || null;
}

/**
 * Check if a custom component is registered for a field type.
 * 
 * @param name - The field type name to check
 */
export function hasFieldComponent(name: string): boolean {
  const registry = getRegistry();
  return registry.has(name);
}

/**
 * Get all registered field component names.
 */
export function getRegisteredFieldTypes(): string[] {
  const registry = getRegistry();
  return Array.from(registry.keys());
}

/**
 * Initialize the registry (called on app load).
 * Ensures the global map exists.
 */
export function initFieldComponentRegistry(): void {
  getRegistry();
  console.log("[Studio] Field component registry initialized");
}

export default {
  registerFieldComponent,
  getFieldComponent,
  hasFieldComponent,
  getRegisteredFieldTypes,
  initFieldComponentRegistry,
};
