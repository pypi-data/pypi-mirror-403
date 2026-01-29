/**
 * Field Component Resolver
 *
 * Resolves the appropriate React component for a field type by checking:
 * 1. Custom registered components (from window.__STUDIO_FIELD_COMPONENTS__)
 * 2. Default components (from DefaultFieldComponents)
 */

import { ComponentType } from "react";
import { getFieldComponent, type FieldComponentProps } from "../../registry/fieldComponents";
import { getDefaultFieldComponent } from "../../registry/defaultComponents";

/**
 * Resolve the appropriate component for a field's ui_widget type.
 *
 * First checks if there's a custom component registered, then falls
 * back to the default component for that type.
 *
 * @param uiWidget - The ui_widget type from FieldTypeInfo
 * @returns The React component to use for this field type
 *
 * @example
 * const Component = resolveFieldComponent('Rating');
 * return <Component value={value} onChange={onChange} {...props} />;
 */
export function resolveFieldComponent(
  uiWidget: string
): ComponentType<FieldComponentProps> {
  // First, check for custom registered component
  const customComponent = getFieldComponent(uiWidget);
  if (customComponent) {
    return customComponent;
  }

  // Fall back to default component
  return getDefaultFieldComponent(uiWidget);
}
