/**
 * DocType Editor Page
 *
 * Visual editor for DocType schema with:
 * - Top bar: Name input + Save button
 * - Left panel: Draggable field list
 * - Right panel: Selected field properties
 */

import {
  useOne,
  useUpdate,
  useCreate,
  useGo,
  useInvalidate,
} from "@refinedev/core";
import { useParams } from "react-router";
import { useState, useCallback, useEffect } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  FieldEditor,
  FieldData,
  FieldTypeInfo,
} from "../../components/FieldEditor";
import { CodePreview } from "../../components/CodePreview";
import { SandboxPreview } from "../../components/SandboxPreview";
import { ControllerEditor } from "../../components/ControllerEditor";
import { useTheme } from "../../providers/theme";

// Types - use FieldData from FieldEditor and extend with stable ID
type FieldDef = FieldData & { _id: string };

interface DocTypeSchema {
  name: string;
  module?: string;
  docstring?: string;
  fields: FieldDef[];
}

/**
 * Extract clean type from Annotated[type, ...] or return as-is
 */
function getCleanType(typeStr: string): string {
  const match = typeStr.match(/^Annotated\[(.*?),/);
  return match ? match[1].trim() : typeStr;
}

/**
 * Format validators for display
 */
function formatValidators(validators?: FieldData["validators"]): string {
  if (!validators) return "";
  const parts: string[] = [];
  if (validators.min_length !== undefined)
    parts.push(`min_length=${validators.min_length}`);
  if (validators.max_length !== undefined)
    parts.push(`max_length=${validators.max_length}`);
  if (validators.pattern) parts.push(`pattern="${validators.pattern}"`);
  if (validators.min_value !== undefined)
    parts.push(`ge=${validators.min_value}`);
  if (validators.max_value !== undefined)
    parts.push(`le=${validators.max_value}`);
  return parts.length > 0 ? `Field(${parts.join(", ")})` : "";
}

interface DocTypeSchema {
  name: string;
  module?: string;
  docstring?: string;
  fields: FieldDef[];
}

// Sortable Field Item Component
function SortableFieldItem({
  field,
  isSelected,
  onSelect,
  onDelete,
  isDark,
}: {
  field: FieldDef;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
  isDark: boolean;
}) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id: field._id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`p-3 rounded-lg border cursor-pointer transition-all ${isSelected
        ? "bg-blue-500/10 border-blue-500"
        : isDark
          ? "bg-zinc-800 border-zinc-700 hover:border-zinc-600"
          : "bg-white border-gray-200 hover:border-gray-300 shadow-sm"
        }`}
      onClick={onSelect}
    >
      <div className="flex items-center gap-3">
        <div
          {...attributes}
          {...listeners}
          className={`cursor-grab ${isDark
            ? "text-zinc-500 hover:text-zinc-400"
            : "text-gray-400 hover:text-gray-600"
            }`}
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M7 2a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 2zm0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 8zm0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 14zm6-8a2 2 0 1 0-.001-4.001A2 2 0 0 0 13 6zm0 2a2 2 0 1 0 .001 4.001A2 2 0 0 0 13 8zm0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 13 14z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <div
            className={`font-medium truncate ${isDark ? "text-white" : "text-gray-900"
              }`}
          >
            {field.name}
          </div>
          <div
            className={`text-sm ${isDark ? "text-zinc-400" : "text-gray-500"}`}
          >
            <div className="font-mono truncate">{getCleanType(field.type)}</div>
            <div className="flex items-center gap-2 text-xs">
              {field.required && <span className="text-red-500">required</span>}
              {formatValidators(field.validators) && (
                <span className="text-green-500 truncate">
                  {formatValidators(field.validators)}
                </span>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={e => {
            e.stopPropagation();
            onDelete();
          }}
          className={`transition-colors ${isDark
            ? "text-zinc-500 hover:text-red-400"
            : "text-gray-400 hover:text-red-500"
            }`}
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
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}

// Main Editor Component
export function DocTypeEdit() {
  const { id } = useParams<{ id: string }>();
  const go = useGo();
  const invalidate = useInvalidate();
  const isCreate = !id;

  // Fetch existing DocType
  const { result, query } = useOne<DocTypeSchema>({
    resource: "doctypes",
    id: id || "",
    queryOptions: { enabled: !isCreate },
  });

  const updateMutation = useUpdate();
  const createMutation = useCreate();

  // Local state
  const [doctype, setDoctype] = useState<DocTypeSchema>(() => ({
    name: "",
    docstring: "",
    fields: [],
  }));
  const [selectedFieldIndex, setSelectedFieldIndex] = useState<number | null>(
    null,
  );
  const [isSaving, setIsSaving] = useState(false);
  const [fieldTypes, setFieldTypes] = useState<FieldTypeInfo[]>([]);
  const { theme } = useTheme();
  const isDark = theme === "dark";

  // Fetch field types from API on mount
  useEffect(() => {
    fetch("/studio/api/field-types")
      .then(res => res.json())
      .then(data => {
        if (data.field_types) {
          setFieldTypes(data.field_types);
        }
      })
      .catch(err => console.error("Failed to fetch field types:", err));
  }, []);

  // Reset state when ID changes (navigation between different doctypes)
  useEffect(() => {
    setDoctype({
      name: "",
      docstring: "",
      fields: [],
    });
    setSelectedFieldIndex(null);
  }, [id]);

  // Initialize from fetched data when it arrives
  // The useOne hook returns { result, query } where result has the data
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rawData = result as any;
  const fetchedDocType = rawData?.data ?? rawData;

  useEffect(() => {
    if (!isCreate && fetchedDocType?.name) {
      console.log("Initializing doctype from API data:", fetchedDocType);
      console.log("Raw API fields:", fetchedDocType.fields);
      // Map API fields to our format (ensure required is boolean and add stable _id)
      const mappedFields = (fetchedDocType.fields || []).map(
        (f: FieldDef, index: number) => {
          console.log("Mapping field:", f.name, "validators:", f.validators);
          return {
            ...f,
            required: f.required ?? true,
            _id: f._id || `field_${Date.now()}_${index}`, // Generate stable ID if not present
          };
        },
      );
      console.log("Mapped fields:", mappedFields);
      setDoctype({
        name: fetchedDocType.name || "",
        docstring: fetchedDocType.docstring || "",
        fields: mappedFields,
      });
    }
  }, [fetchedDocType, isCreate]);

  // DnD sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  // Handlers
  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setDoctype(prev => {
        const oldIndex = prev.fields.findIndex(f => f._id === active.id);
        const newIndex = prev.fields.findIndex(f => f._id === over.id);
        return { ...prev, fields: arrayMove(prev.fields, oldIndex, newIndex) };
      });
    }
  }, []);

  const handleAddField = useCallback(() => {
    let newIndex = 0;
    setDoctype(prev => {
      const newName = `field_${prev.fields.length + 1}`;
      const newField: FieldDef = {
        name: newName,
        type: "str",
        required: true,
        _id: `field_${Date.now()}_${prev.fields.length}`,
      };
      newIndex = prev.fields.length; // Store the index before adding
      return {
        ...prev,
        fields: [...prev.fields, newField],
      };
    });
    setSelectedFieldIndex(newIndex);
  }, []);

  const handleDeleteField = useCallback((index: number) => {
    setDoctype(prev => ({
      ...prev,
      fields: prev.fields.filter((_, i) => i !== index),
    }));
    setSelectedFieldIndex(null);
  }, []);

  const handleFieldChange = useCallback(
    (updatedField: FieldData) => {
      // Accept FieldData (without _id)
      if (selectedFieldIndex === null || selectedFieldIndex < 0) return;
      setDoctype(prev => ({
        ...prev,
        fields: prev.fields.map((f, i) =>
          i === selectedFieldIndex
            ? { ...updatedField, _id: f._id } // Add back the stable _id
            : f,
        ),
      }));
    },
    [selectedFieldIndex],
  );

  const handleSave = useCallback(() => {
    if (!doctype.name.trim()) {
      alert("DocType name is required");
      return;
    }

    setIsSaving(true);
    // Strip out _id field before sending to backend (it's only for frontend tracking)
    const payload = {
      name: doctype.name,
      docstring: doctype.docstring,
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      fields: doctype.fields.map(({ _id, ...field }) => field),
    };

    // Debug: log what's being sent
    console.log("Save payload:", JSON.stringify(payload, null, 2));

    const options = {
      onSuccess: () => {
        setIsSaving(false);
        // Invalidate cache to ensure fresh data on next load
        invalidate({
          resource: "doctypes",
          invalidates: ["list", "detail"],
        });
        go({ to: "/doctypes" });
      },
      onError: () => {
        setIsSaving(false);
        alert("Failed to save DocType");
      },
    };

    if (isCreate) {
      createMutation.mutate(
        { resource: "doctypes", values: payload, invalidates: [] },
        options,
      );
    } else {
      // Manually invalidate after update to ensure fresh data
      updateMutation.mutate(
        { resource: "doctypes", id: id!, values: payload, invalidates: [] },
        options,
      );
    }
  }, [doctype, isCreate, id, createMutation, updateMutation, go, invalidate]);

  const isLoading = !isCreate && query.isLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Top Bar */}
      <div
        className={`flex items-center justify-between p-4 border-b ${isDark ? "border-zinc-700 bg-zinc-800/50" : "border-gray-200 bg-white"
          }`}
      >
        <div className="flex items-center gap-4">
          <button
            onClick={() => go({ to: "/doctypes" })}
            className={`transition-colors ${isDark
              ? "text-zinc-400 hover:text-white"
              : "text-gray-400 hover:text-gray-600"
              }`}
          >
            <svg
              className="w-6 h-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>
          <input
            type="text"
            value={doctype.name}
            onChange={e =>
              setDoctype(prev => ({ ...prev, name: e.target.value }))
            }
            placeholder="DocType Name"
            className={`text-xl font-bold bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1 ${isDark
              ? "text-white placeholder-zinc-500"
              : "text-gray-900 placeholder-gray-400"
              }`}
          />
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving || !doctype.name}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors shadow-sm flex items-center gap-2"
        >
          {isSaving ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
          ) : (
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
                d="M5 13l4 4L19 7"
              />
            </svg>
          )}
          Save
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: Field List */}
        <div
          className={`w-80 border-r flex flex-col ${isDark
            ? "border-zinc-700 bg-zinc-800/30"
            : "border-gray-200 bg-gray-50"
            }`}
        >
          <div
            className={`px-4 h-14 border-b flex items-center justify-between ${isDark ? "border-zinc-700" : "border-gray-200"
              }`}
          >
            <h2
              className={`font-semibold ${isDark ? "text-white" : "text-gray-900"
                }`}
            >
              Fields
            </h2>
            <button
              onClick={handleAddField}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm"
            >
              + Add Field
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={doctype.fields.map(f => f._id)}
                strategy={verticalListSortingStrategy}
              >
                <div className="space-y-2">
                  {doctype.fields.map((field, index) => (
                    <SortableFieldItem
                      key={field._id}
                      field={field}
                      isSelected={selectedFieldIndex === index}
                      onSelect={() => setSelectedFieldIndex(index)}
                      onDelete={() => handleDeleteField(index)}
                      isDark={isDark}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
            {doctype.fields.length === 0 && (
              <div
                className={`text-center py-8 ${isDark ? "text-zinc-500" : "text-gray-500"
                  }`}
              >
                No fields yet. Click "Add Field" to start.
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Field Properties / Code Preview */}
        <div
          className={`flex-1 flex flex-col overflow-hidden ${isDark ? "bg-zinc-900/50" : "bg-white"
            }`}
        >
          {/* Tab buttons */}
          <div
            className={`flex items-center h-14 border-b ${isDark ? "border-zinc-700" : "border-gray-200"
              }`}
          >
            <button
              onClick={() =>
                setSelectedFieldIndex(
                  selectedFieldIndex !== null ? selectedFieldIndex : 0,
                )
              }
              className={`px-4 h-full inline-flex items-center text-sm font-medium transition-colors ${selectedFieldIndex !== null
                ? "text-blue-500 border-b-2 border-blue-500"
                : isDark
                  ? "text-zinc-400 hover:text-zinc-300"
                  : "text-gray-500 hover:text-gray-700"
                }`}
            >
              Properties
            </button>
            <button
              onClick={() => setSelectedFieldIndex(null)}
              className={`px-4 h-full inline-flex items-center text-sm font-medium transition-colors ${selectedFieldIndex === null
                ? "text-blue-500 border-b-2 border-blue-500"
                : isDark
                  ? "text-zinc-400 hover:text-zinc-300"
                  : "text-gray-500 hover:text-gray-700"
                }`}
            >
              Code Preview
            </button>
            <button
              onClick={() => setSelectedFieldIndex(-1)}
              className={`px-4 h-full inline-flex items-center text-sm font-medium transition-colors ${selectedFieldIndex === -1
                ? "text-blue-500 border-b-2 border-blue-500"
                : isDark
                  ? "text-zinc-400 hover:text-zinc-300"
                  : "text-gray-500 hover:text-gray-700"
                }`}
            >
              Sandbox
            </button>
            <button
              onClick={() => setSelectedFieldIndex(-2)}
              className={`px-4 h-full inline-flex items-center text-sm font-medium transition-colors ${selectedFieldIndex === -2
                ? "text-blue-500 border-b-2 border-blue-500"
                : isDark
                  ? "text-zinc-400 hover:text-zinc-300"
                  : "text-gray-500 hover:text-gray-700"
                }`}
            >
              Controller
            </button>
          </div>
          {/* Panel content */}
          <div className="flex-1 overflow-hidden">
            {selectedFieldIndex !== null && selectedFieldIndex >= 0 ? (
              <div className="h-full overflow-y-auto">
                <FieldEditor
                  key={selectedFieldIndex} // Force remount when selected field changes
                  field={doctype.fields[selectedFieldIndex]}
                  fieldTypes={fieldTypes}
                  onChange={handleFieldChange}
                />
              </div>
            ) : selectedFieldIndex === -1 ? (
              <SandboxPreview
                fields={doctype.fields}
                doctypeName={doctype.name || "DocType"}
              />
            ) : selectedFieldIndex === -2 ? (
              <ControllerEditor doctypeName={doctype.name || "DocType"} />
            ) : (
              <CodePreview schema={doctype} className="h-full" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DocTypeEdit;
