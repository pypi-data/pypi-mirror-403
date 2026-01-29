/**
 * Module Explorer Component
 * 
 * Tree view navigation for DocTypes grouped by directory/module.
 * Features:
 * - Hierarchical folder structure
 * - Expand/collapse directories
 * - Click to navigate to DocType
 */

import { useState, useMemo } from "react";
import { useList, useGo } from "@refinedev/core";

interface DocTypeRecord {
  name: string;
  module: string;
  file_path: string;
}

interface TreeNode {
  name: string;
  path: string;
  isDirectory: boolean;
  children: TreeNode[];
  doctype?: DocTypeRecord;
}

interface ModuleExplorerProps {
  className?: string;
}

// Build tree structure from flat list of doctypes
function buildTree(doctypes: DocTypeRecord[]): TreeNode[] {
  const root: TreeNode[] = [];
  
  doctypes.forEach((doctype) => {
    // Parse file path into segments
    const segments = doctype.file_path.split("/").filter(Boolean);
    let currentLevel = root;
    let currentPath = "";
    
    // Navigate/create directory nodes
    for (let i = 0; i < segments.length - 1; i++) {
      const segment = segments[i];
      currentPath += "/" + segment;
      
      let node = currentLevel.find((n) => n.name === segment && n.isDirectory);
      if (!node) {
        node = {
          name: segment,
          path: currentPath,
          isDirectory: true,
          children: [],
        };
        currentLevel.push(node);
      }
      currentLevel = node.children;
    }
    
    // Add doctype node (leaf)
    currentLevel.push({
      name: doctype.name,
      path: doctype.file_path,
      isDirectory: false,
      children: [],
      doctype,
    });
  });
  
  // Sort: directories first, then alphabetically
  const sortNodes = (nodes: TreeNode[]): TreeNode[] => {
    return nodes
      .sort((a, b) => {
        if (a.isDirectory && !b.isDirectory) return -1;
        if (!a.isDirectory && b.isDirectory) return 1;
        return a.name.localeCompare(b.name);
      })
      .map((node) => ({
        ...node,
        children: sortNodes(node.children),
      }));
  };
  
  return sortNodes(root);
}

// Tree Node Component
function TreeNodeItem({
  node,
  level,
  expandedPaths,
  onToggle,
  onSelect,
}: {
  node: TreeNode;
  level: number;
  expandedPaths: Set<string>;
  onToggle: (path: string) => void;
  onSelect: (doctype: DocTypeRecord) => void;
}) {
  const isExpanded = expandedPaths.has(node.path);
  const hasChildren = node.children.length > 0;
  const paddingLeft = level * 16 + 8;

  return (
    <>
      <button
        onClick={() => {
          if (node.isDirectory) {
            onToggle(node.path);
          } else if (node.doctype) {
            onSelect(node.doctype);
          }
        }}
        className={`w-full flex items-center gap-2 px-2 py-1.5 text-sm text-left hover:bg-slate-700/50 transition-colors ${
          !node.isDirectory ? "text-slate-300" : "text-slate-400"
        }`}
        style={{ paddingLeft }}
      >
        {/* Expand/Collapse Icon */}
        {node.isDirectory ? (
          <svg
            className={`w-4 h-4 text-slate-500 transition-transform ${
              isExpanded ? "rotate-90" : ""
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        ) : (
          <span className="w-4" />
        )}

        {/* Icon */}
        {node.isDirectory ? (
          <svg className="w-4 h-4 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M2 6a2 2 0 012-2h4l2 2h6a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"
              clipRule="evenodd"
            />
          </svg>
        ) : (
          <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        )}

        {/* Name */}
        <span className="truncate">{node.name}</span>

        {/* Badge for directory count */}
        {node.isDirectory && hasChildren && (
          <span className="ml-auto text-xs text-slate-500 bg-slate-700 px-1.5 py-0.5 rounded">
            {node.children.length}
          </span>
        )}
      </button>

      {/* Children */}
      {node.isDirectory && isExpanded && (
        <div>
          {node.children.map((child) => (
            <TreeNodeItem
              key={child.path}
              node={child}
              level={level + 1}
              expandedPaths={expandedPaths}
              onToggle={onToggle}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </>
  );
}

export function ModuleExplorer({ className = "" }: ModuleExplorerProps) {
  const go = useGo();
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set([""]));
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch all doctypes
  const { result, query } = useList<DocTypeRecord>({
    resource: "doctypes",
  });

  const doctypes = useMemo(() => result?.data ?? [], [result?.data]);
  
  // Filter by search
  const filteredDoctypes = useMemo(() => {
    if (!searchQuery.trim()) return doctypes;
    const q = searchQuery.toLowerCase();
    return doctypes.filter(
      (d) => d.name.toLowerCase().includes(q) || d.module.toLowerCase().includes(q)
    );
  }, [doctypes, searchQuery]);

  // Build tree
  const tree = useMemo(() => buildTree(filteredDoctypes), [filteredDoctypes]);

  const handleToggle = (path: string) => {
    setExpandedPaths((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const handleSelect = (doctype: DocTypeRecord) => {
    go({ to: `/doctypes/edit/${doctype.name}` });
  };

  const expandAll = () => {
    const allPaths = new Set<string>();
    const collect = (nodes: TreeNode[]) => {
      nodes.forEach((n) => {
        if (n.isDirectory) {
          allPaths.add(n.path);
          collect(n.children);
        }
      });
    };
    collect(tree);
    setExpandedPaths(allPaths);
  };

  const collapseAll = () => {
    setExpandedPaths(new Set());
  };

  return (
    <div className={`flex flex-col h-full bg-slate-800/50 ${className}`}>
      {/* Header */}
      <div className="p-3 border-b border-slate-700">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-white text-sm">Explorer</h3>
          <div className="flex gap-1">
            <button
              onClick={expandAll}
              className="p-1 text-slate-500 hover:text-slate-300 transition-colors"
              title="Expand All"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            </button>
            <button
              onClick={collapseAll}
              className="p-1 text-slate-500 hover:text-slate-300 transition-colors"
              title="Collapse All"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
          </div>
        </div>
        <input
          type="text"
          placeholder="Search..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-2 py-1 text-sm bg-slate-900 border border-slate-700 rounded text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto py-2">
        {query.isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400" />
          </div>
        ) : tree.length === 0 ? (
          <div className="text-center text-slate-500 text-sm py-8">
            {searchQuery ? "No matches found" : "No DocTypes found"}
          </div>
        ) : (
          tree.map((node) => (
            <TreeNodeItem
              key={node.path}
              node={node}
              level={0}
              expandedPaths={expandedPaths}
              onToggle={handleToggle}
              onSelect={handleSelect}
            />
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-slate-700 text-xs text-slate-500">
        {doctypes.length} DocTypes
      </div>
    </div>
  );
}

export default ModuleExplorer;
