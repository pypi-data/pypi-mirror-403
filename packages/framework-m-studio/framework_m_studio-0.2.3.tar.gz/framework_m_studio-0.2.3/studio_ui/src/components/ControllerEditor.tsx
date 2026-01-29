/**
 * ControllerEditor Component
 * 
 * UI for viewing and editing controller hook methods.
 * Shows available lifecycle hooks with their descriptions
 * and allows editing method bodies.
 */

import { useState, useCallback } from "react";

/**
 * Hook method definition
 */
interface HookMethod {
  name: string;
  description: string;
  signature: string;
  body: string;
  isCustom?: boolean;
}

/**
 * Default lifecycle hooks for controllers
 */
const DEFAULT_HOOKS: HookMethod[] = [
  {
    name: "validate",
    description: "Validate document before saving. Raise ValueError for validation errors.",
    signature: "async def validate(self, doc: DocType) -> None:",
    body: "        pass",
  },
  {
    name: "before_save",
    description: "Called before persisting to database. Use for computed fields.",
    signature: "async def before_save(self, doc: DocType) -> None:",
    body: "        pass",
  },
  {
    name: "after_save",
    description: "Called after successful save. Use for side effects like notifications.",
    signature: "async def after_save(self, doc: DocType) -> None:",
    body: "        pass",
  },
  {
    name: "before_delete",
    description: "Called before deleting. Use for cleanup or validation.",
    signature: "async def before_delete(self, doc: DocType) -> None:",
    body: "        pass",
  },
];

interface ControllerEditorProps {
  /** DocType name for the controller */
  doctypeName: string;
  /** Initial hook methods (parsed from existing controller) */
  initialHooks?: HookMethod[];
  /** Callback when hooks change */
  onChange?: (hooks: HookMethod[]) => void;
  /** Read-only mode */
  readOnly?: boolean;
}

export function ControllerEditor({
  doctypeName,
  initialHooks,
  onChange,
  readOnly = false,
}: ControllerEditorProps) {
  const [hooks, setHooks] = useState<HookMethod[]>(
    initialHooks || DEFAULT_HOOKS.map(h => ({
      ...h,
      signature: h.signature.replace("DocType", doctypeName),
    }))
  );
  const [selectedHook, setSelectedHook] = useState<string | null>(null);
  const [editingBody, setEditingBody] = useState<string>("");
  const [showAddCustom, setShowAddCustom] = useState(false);
  const [customMethodName, setCustomMethodName] = useState("");

  // Handle hook selection
  const handleSelectHook = useCallback((hookName: string) => {
    const hook = hooks.find(h => h.name === hookName);
    if (hook) {
      setSelectedHook(hookName);
      setEditingBody(hook.body);
    }
  }, [hooks]);

  // Handle body change
  const handleBodyChange = useCallback((newBody: string) => {
    setEditingBody(newBody);
    
    const updatedHooks = hooks.map(h => 
      h.name === selectedHook ? { ...h, body: newBody } : h
    );
    setHooks(updatedHooks);
    onChange?.(updatedHooks);
  }, [hooks, selectedHook, onChange]);

  // Add custom method
  const handleAddCustomMethod = useCallback(() => {
    if (!customMethodName.trim()) return;

    const snakeName = customMethodName.toLowerCase().replace(/\s+/g, "_");
    const newMethod: HookMethod = {
      name: snakeName,
      description: "Custom method",
      signature: `async def ${snakeName}(self, doc: ${doctypeName}) -> None:`,
      body: "        # Add your custom logic here\n        pass",
      isCustom: true,
    };

    const updatedHooks = [...hooks, newMethod];
    setHooks(updatedHooks);
    onChange?.(updatedHooks);
    setCustomMethodName("");
    setShowAddCustom(false);
    setSelectedHook(snakeName);
    setEditingBody(newMethod.body);
  }, [customMethodName, doctypeName, hooks, onChange]);

  // Delete custom method
  const handleDeleteMethod = useCallback((hookName: string) => {
    const hook = hooks.find(h => h.name === hookName);
    if (!hook?.isCustom) return; // Only delete custom methods

    if (confirm(`Delete method "${hookName}"?`)) {
      const updatedHooks = hooks.filter(h => h.name !== hookName);
      setHooks(updatedHooks);
      onChange?.(updatedHooks);
      if (selectedHook === hookName) {
        setSelectedHook(null);
        setEditingBody("");
      }
    }
  }, [hooks, selectedHook, onChange]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-zinc-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {doctypeName}Controller
        </h3>
        <p className="text-sm text-gray-500 dark:text-zinc-400">
          Edit lifecycle hooks and custom methods
        </p>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Methods List */}
        <div className="w-64 border-r border-gray-200 dark:border-zinc-700 flex flex-col">
          <div className="flex-1 overflow-auto">
            <div className="px-3 py-2 text-xs font-medium text-gray-500 dark:text-zinc-400 uppercase tracking-wider">
              Lifecycle Hooks
            </div>
            {hooks.filter(h => !h.isCustom).map((hook) => (
              <button
                key={hook.name}
                onClick={() => handleSelectHook(hook.name)}
                className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                  selectedHook === hook.name
                    ? "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400"
                    : "text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-800"
                }`}
              >
                <div className="font-medium">{hook.name}</div>
                <div className="text-xs text-gray-500 dark:text-zinc-500 truncate">
                  {hook.description}
                </div>
              </button>
            ))}

            {/* Custom Methods */}
            {hooks.some(h => h.isCustom) && (
              <>
                <div className="px-3 py-2 mt-2 text-xs font-medium text-gray-500 dark:text-zinc-400 uppercase tracking-wider border-t border-gray-200 dark:border-zinc-700">
                  Custom Methods
                </div>
                {hooks.filter(h => h.isCustom).map((hook) => (
                  <div
                    key={hook.name}
                    className={`flex items-center justify-between px-3 py-2 text-sm transition-colors ${
                      selectedHook === hook.name
                        ? "bg-blue-50 dark:bg-blue-900/20"
                        : "hover:bg-gray-50 dark:hover:bg-zinc-800"
                    }`}
                  >
                    <button
                      onClick={() => handleSelectHook(hook.name)}
                      className={`flex-1 text-left ${
                        selectedHook === hook.name
                          ? "text-blue-600 dark:text-blue-400"
                          : "text-gray-700 dark:text-zinc-300"
                      }`}
                    >
                      {hook.name}
                    </button>
                    {!readOnly && (
                      <button
                        onClick={() => handleDeleteMethod(hook.name)}
                        className="p-1 text-gray-400 hover:text-red-500 dark:text-zinc-500"
                        title="Delete method"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
              </>
            )}
          </div>

          {/* Add Custom Method */}
          {!readOnly && (
            <div className="p-3 border-t border-gray-200 dark:border-zinc-700">
              {showAddCustom ? (
                <div className="space-y-2">
                  <input
                    type="text"
                    value={customMethodName}
                    onChange={(e) => setCustomMethodName(e.target.value)}
                    placeholder="method_name"
                    className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-zinc-600 rounded bg-white dark:bg-zinc-800 text-gray-900 dark:text-white"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleAddCustomMethod();
                      if (e.key === "Escape") setShowAddCustom(false);
                    }}
                  />
                  <div className="flex gap-1">
                    <button
                      onClick={handleAddCustomMethod}
                      className="flex-1 px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Add
                    </button>
                    <button
                      onClick={() => setShowAddCustom(false)}
                      className="flex-1 px-2 py-1 text-xs border border-gray-300 dark:border-zinc-600 rounded hover:bg-gray-100 dark:hover:bg-zinc-700"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowAddCustom(true)}
                  className="w-full flex items-center justify-center gap-1 px-3 py-1.5 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Add Method
                </button>
              )}
            </div>
          )}
        </div>

        {/* Code Editor */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {selectedHook ? (
            <>
              {/* Method Signature */}
              <div className="px-4 py-2 bg-gray-50 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700">
                <code className="text-sm font-mono text-purple-600 dark:text-purple-400">
                  {hooks.find(h => h.name === selectedHook)?.signature}
                </code>
              </div>

              {/* Method Body Editor */}
              <div className="flex-1 overflow-auto">
                <textarea
                  value={editingBody}
                  onChange={(e) => handleBodyChange(e.target.value)}
                  disabled={readOnly}
                  className="w-full h-full p-4 font-mono text-sm bg-gray-900 text-green-400 resize-none focus:outline-none"
                  placeholder="        # Add your code here"
                  spellCheck={false}
                />
              </div>

              {/* Help Text */}
              <div className="px-4 py-2 bg-gray-50 dark:bg-zinc-800 border-t border-gray-200 dark:border-zinc-700 text-xs text-gray-500 dark:text-zinc-400">
                {hooks.find(h => h.name === selectedHook)?.description}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400 dark:text-zinc-500">
              <div className="text-center">
                <svg className="w-12 h-12 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                <p>Select a method to edit</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ControllerEditor;
