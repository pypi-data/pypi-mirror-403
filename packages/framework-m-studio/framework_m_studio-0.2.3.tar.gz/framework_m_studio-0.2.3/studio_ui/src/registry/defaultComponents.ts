import { type FieldComponentProps } from "./fieldComponents";
import {
    DefaultTextInput,
    DefaultTextArea,
    DefaultNumberInput,
    DefaultCheckbox,
    DefaultSelect,
    DefaultDateInput,
    DefaultDateTimeInput,
    DefaultJSONEditor,
} from "../components/fields/DefaultFieldComponents";

// Map of field type names to their default components
export const defaultFieldComponents: Record<string, React.ComponentType<FieldComponentProps>> = {
    text: DefaultTextInput,
    textarea: DefaultTextArea,
    number: DefaultNumberInput,
    checkbox: DefaultCheckbox,
    select: DefaultSelect,
    date: DefaultDateInput,
    datetime: DefaultDateTimeInput,
    json: DefaultJSONEditor,
    email: DefaultTextInput,
    url: DefaultTextInput,
};

/**
 * Get default component for a ui_widget type
 */
export function getDefaultFieldComponent(
    uiWidget: string
): React.ComponentType<FieldComponentProps> {
    return defaultFieldComponents[uiWidget] || DefaultTextInput;
}
