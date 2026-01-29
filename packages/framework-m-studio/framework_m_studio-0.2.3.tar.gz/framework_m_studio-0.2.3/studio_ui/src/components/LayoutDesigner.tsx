/**
 * Layout Designer Component
 * 
 * Visual form layout designer with:
 * - Sections with configurable columns (1/2/3)
 * - Drag fields into grid cells
 * - Real-time form preview
 */

import { useState, useCallback } from "react";
import {
  DndContext,
  closestCenter,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  useDroppable,
  useDraggable,
} from "@dnd-kit/core";

// Types
interface FieldData {
  name: string;
  type: string;
  required: boolean;
}

interface LayoutCell {
  fieldName: string | null;
  colspan?: number;
}

interface LayoutSection {
  id: string;
  title: string;
  columns: 1 | 2 | 3;
  cells: LayoutCell[];
}

interface LayoutDesignerProps {
  fields: FieldData[];
  layout: LayoutSection[];
  onChange: (layout: LayoutSection[]) => void;
}

// Draggable Field Component (from field palette)
function DraggableField({ field }: { field: FieldData }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `field-${field.name}`,
    data: { type: "field", field },
  });

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className={`p-2 bg-slate-800 border border-slate-700 rounded cursor-grab text-sm ${
        isDragging ? "opacity-50" : ""
      }`}
    >
      <span className="text-white">{field.name}</span>
      <span className="text-slate-500 ml-2 font-mono text-xs">{field.type}</span>
    </div>
  );
}

// Droppable Cell Component
function DroppableCell({
  sectionId,
  cellIndex,
  cell,
  columns,
}: {
  sectionId: string;
  cellIndex: number;
  cell: LayoutCell;
  columns: 1 | 2 | 3;
}) {
  const { isOver, setNodeRef } = useDroppable({
    id: `cell-${sectionId}-${cellIndex}`,
    data: { type: "cell", sectionId, cellIndex },
  });

  const widthClass = {
    1: "w-full",
    2: "w-1/2",
    3: "w-1/3",
  }[columns];

  return (
    <div
      ref={setNodeRef}
      className={`${widthClass} p-2`}
    >
      <div
        className={`min-h-[60px] border-2 border-dashed rounded-lg flex items-center justify-center transition-colors ${
          isOver
            ? "border-blue-500 bg-blue-500/10"
            : cell.fieldName
            ? "border-slate-600 bg-slate-800"
            : "border-slate-700 bg-slate-900/50"
        }`}
      >
        {cell.fieldName ? (
          <div className="px-3 py-2 text-white text-sm">
            {cell.fieldName}
          </div>
        ) : (
          <span className="text-slate-600 text-sm">Drop field here</span>
        )}
      </div>
    </div>
  );
}

// Section Component
function LayoutSectionComponent({
  section,
  onUpdateSection,
  onDeleteSection,
}: {
  section: LayoutSection;
  onUpdateSection: (section: LayoutSection) => void;
  onDeleteSection: () => void;
}) {
  const handleColumnChange = (columns: 1 | 2 | 3) => {
    // Resize cells array to match new column count
    const newCells: LayoutCell[] = [];
    for (let i = 0; i < columns; i++) {
      newCells.push(section.cells[i] || { fieldName: null });
    }
    onUpdateSection({ ...section, columns, cells: newCells });
  };

  return (
    <div className="border border-slate-700 rounded-lg overflow-hidden mb-4">
      {/* Section Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800">
        <input
          type="text"
          value={section.title}
          onChange={(e) => onUpdateSection({ ...section, title: e.target.value })}
          className="bg-transparent text-white font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 rounded px-1"
          placeholder="Section Title"
        />
        <div className="flex items-center gap-2">
          {/* Column selector */}
          <div className="flex gap-1">
            {([1, 2, 3] as const).map((cols) => (
              <button
                key={cols}
                onClick={() => handleColumnChange(cols)}
                className={`w-8 h-8 rounded text-xs font-medium transition-colors ${
                  section.columns === cols
                    ? "bg-blue-600 text-white"
                    : "bg-slate-700 text-slate-400 hover:bg-slate-600"
                }`}
              >
                {cols}
              </button>
            ))}
          </div>
          <button
            onClick={onDeleteSection}
            className="text-slate-500 hover:text-red-400 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Grid Cells */}
      <div className="flex flex-wrap p-2 bg-slate-900/50">
        {section.cells.map((cell, index) => (
          <DroppableCell
            key={index}
            sectionId={section.id}
            cellIndex={index}
            cell={cell}
            columns={section.columns}
          />
        ))}
      </div>
    </div>
  );
}

// Form Preview Component
function FormPreview({ layout, fields }: { layout: LayoutSection[]; fields: FieldData[] }) {
  const fieldMap = Object.fromEntries(fields.map((f) => [f.name, f]));

  return (
    <div className="p-4 bg-white rounded-lg">
      {layout.map((section) => (
        <div key={section.id} className="mb-6">
          {section.title && (
            <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">
              {section.title}
            </h3>
          )}
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${section.columns}, 1fr)` }}>
            {section.cells.map((cell, index) => {
              if (!cell.fieldName) return <div key={index} />;
              const field = fieldMap[cell.fieldName];
              if (!field) return <div key={index} />;
              
              return (
                <div key={index}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {field.name}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <input
                    type="text"
                    disabled
                    placeholder={field.type}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                  />
                </div>
              );
            })}
          </div>
        </div>
      ))}
      {layout.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          Add sections to see form preview
        </div>
      )}
    </div>
  );
}

export function LayoutDesigner({ fields, layout, onChange }: LayoutDesignerProps) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  // Get unassigned fields
  const assignedFields = new Set(
    layout.flatMap((s) => s.cells.map((c) => c.fieldName).filter(Boolean))
  );
  const unassignedFields = fields.filter((f) => !assignedFields.has(f.name));

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    setActiveId(null);
    const { active, over } = event;
    
    if (!over || !active.data.current) return;
    
    const activeData = active.data.current as { type: string; field?: FieldData };
    const overData = over.data.current as { type: string; sectionId?: string; cellIndex?: number };
    
    if (activeData.type === "field" && overData.type === "cell" && activeData.field) {
      const newLayout = layout.map((section) => {
        if (section.id === overData.sectionId) {
          const newCells = [...section.cells];
          newCells[overData.cellIndex!] = { fieldName: activeData.field!.name };
          return { ...section, cells: newCells };
        }
        return section;
      });
      onChange(newLayout);
    }
  }, [layout, onChange]);

  const addSection = () => {
    const newSection: LayoutSection = {
      id: `section-${Date.now()}`,
      title: "New Section",
      columns: 2,
      cells: [{ fieldName: null }, { fieldName: null }],
    };
    onChange([...layout, newSection]);
  };

  const updateSection = (index: number, section: LayoutSection) => {
    const newLayout = [...layout];
    newLayout[index] = section;
    onChange(newLayout);
  };

  const deleteSection = (index: number) => {
    onChange(layout.filter((_, i) => i !== index));
  };

  return (
    <DndContext
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex h-full">
        {/* Left: Field Palette */}
        <div className="w-64 border-r border-slate-700 flex flex-col bg-slate-800/30">
          <div className="p-4 border-b border-slate-700">
            <h3 className="font-semibold text-white">Fields</h3>
            <p className="text-xs text-slate-500 mt-1">Drag to layout</p>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {unassignedFields.map((field) => (
              <DraggableField key={field.name} field={field} />
            ))}
            {unassignedFields.length === 0 && (
              <p className="text-slate-500 text-sm text-center py-4">
                All fields assigned
              </p>
            )}
          </div>
        </div>

        {/* Center: Layout Canvas */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Toolbar */}
          <div className="flex items-center justify-between p-4 border-b border-slate-700">
            <h3 className="font-semibold text-white">Layout Designer</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowPreview(!showPreview)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  showPreview
                    ? "bg-blue-600 text-white"
                    : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                }`}
              >
                {showPreview ? "Edit" : "Preview"}
              </button>
              <button
                onClick={addSection}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
              >
                + Add Section
              </button>
            </div>
          </div>

          {/* Canvas */}
          <div className="flex-1 overflow-y-auto p-4">
            {showPreview ? (
              <FormPreview layout={layout} fields={fields} />
            ) : (
              <>
                {layout.map((section, index) => (
                  <LayoutSectionComponent
                    key={section.id}
                    section={section}
                    onUpdateSection={(s) => updateSection(index, s)}
                    onDeleteSection={() => deleteSection(index)}
                  />
                ))}
                {layout.length === 0 && (
                  <div className="text-center text-slate-500 py-12 border-2 border-dashed border-slate-700 rounded-lg">
                    Click "Add Section" to start designing your form layout
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        <DragOverlay>
          {activeId && activeId.startsWith("field-") && (
            <div className="p-2 bg-blue-600 border border-blue-500 rounded text-sm text-white shadow-lg">
              {activeId.replace("field-", "")}
            </div>
          )}
        </DragOverlay>
      </div>
    </DndContext>
  );
}

export default LayoutDesigner;
