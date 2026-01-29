/**
 * Field Components - Public API
 *
 * Exports default field components and resolver.
 */

export {
  DefaultTextInput,
  DefaultTextArea,
  DefaultNumberInput,
  DefaultCheckbox,
  DefaultSelect,
  DefaultDateInput,
  DefaultDateTimeInput,
  DefaultJSONEditor,
} from "./DefaultFieldComponents";

export {
  defaultFieldComponents,
  getDefaultFieldComponent,
} from "../../registry/defaultComponents";

export { resolveFieldComponent } from "./resolveFieldComponent.ts";
