/**
 * ERD/Mind Map View Component
 * 
 * Displays DocType relationships as a visual graph:
 * - Central node: Current DocType
 * - Connected nodes: Related DocTypes via Link fields
 * - Interactive: Drag to connect creates Link fields
 */

import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Node,
  Edge,
  Handle,
  Position,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

interface FieldData {
  name: string;
  type: string;
  required: boolean;
  description?: string;
}

interface DocTypeData {
  name: string;
  fields: FieldData[];
  docstring?: string;
}

interface ERDViewProps {
  currentDocType: DocTypeData;
  relatedDocTypes?: DocTypeData[];
  onConnect?: (source: string, target: string) => void;
}

// Custom node for DocType
function DocTypeNode({ data }: { data: { label: string; fields: FieldData[]; isMain: boolean } }) {
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-[200px] ${
        data.isMain
          ? "bg-blue-600/30 border-blue-500 shadow-lg shadow-blue-500/20"
          : "bg-slate-800 border-slate-600"
      }`}
    >
      <Handle type="target" position={Position.Left} className="!bg-blue-500" />
      <div className="font-semibold text-white text-center mb-2">{data.label}</div>
      <div className="space-y-1 max-h-40 overflow-y-auto">
        {data.fields.slice(0, 5).map((field) => (
          <div
            key={field.name}
            className="text-xs px-2 py-1 bg-slate-900/50 rounded flex justify-between"
          >
            <span className="text-slate-300">{field.name}</span>
            <span className="text-slate-500 font-mono">{field.type}</span>
          </div>
        ))}
        {data.fields.length > 5 && (
          <div className="text-xs text-slate-500 text-center">
            +{data.fields.length - 5} more
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-green-500" />
    </div>
  );
}

const nodeTypes = {
  doctype: DocTypeNode,
};

export function ERDView({ currentDocType, relatedDocTypes = [], onConnect }: ERDViewProps) {
  // Build nodes from DocType data
  const initialNodes = useMemo((): Node[] => {
    const nodes: Node[] = [];
    
    // Central node (current DocType)
    nodes.push({
      id: currentDocType.name,
      type: "doctype",
      position: { x: 300, y: 200 },
      data: {
        label: currentDocType.name,
        fields: currentDocType.fields,
        isMain: true,
      },
    });
    
    // Related DocType nodes (arranged in a circle)
    const angleStep = (2 * Math.PI) / Math.max(relatedDocTypes.length, 1);
    const radius = 250;
    
    relatedDocTypes.forEach((doctype, index) => {
      const angle = angleStep * index - Math.PI / 2;
      nodes.push({
        id: doctype.name,
        type: "doctype",
        position: {
          x: 300 + radius * Math.cos(angle),
          y: 200 + radius * Math.sin(angle),
        },
        data: {
          label: doctype.name,
          fields: doctype.fields,
          isMain: false,
        },
      });
    });
    
    return nodes;
  }, [currentDocType, relatedDocTypes]);

  // Build edges from Link fields
  const initialEdges = useMemo((): Edge[] => {
    const edges: Edge[] = [];
    
    // Find Link fields in current DocType that reference other DocTypes
    currentDocType.fields.forEach((field) => {
      // Check if field type is a Link to another DocType
      const linkMatch = field.type.match(/Link\[(\w+)\]/);
      if (linkMatch) {
        const targetDocType = linkMatch[1];
        edges.push({
          id: `${currentDocType.name}-${field.name}-${targetDocType}`,
          source: currentDocType.name,
          target: targetDocType,
          label: field.name,
          animated: true,
          style: { stroke: "#60a5fa" },
        });
      }
    });
    
    return edges;
  }, [currentDocType]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const handleConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge({ ...params, animated: true }, eds));
      if (onConnect && params.source && params.target) {
        onConnect(params.source, params.target);
      }
    },
    [setEdges, onConnect]
  );

  return (
    <div className="h-full w-full bg-slate-900">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={handleConnect}
        nodeTypes={nodeTypes}
        fitView
        className="touchdevice-flow"
        proOptions={{ hideAttribution: true }}
      >
        <Controls className="!bg-slate-800 !border-slate-700 !rounded-lg" />
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#334155" />
      </ReactFlow>
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 p-3 bg-slate-800/90 rounded-lg border border-slate-700 text-xs">
        <div className="font-medium text-slate-300 mb-2">Legend</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-blue-500/30 border border-blue-500" />
            <span className="text-slate-400">Current DocType</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-slate-800 border border-slate-600" />
            <span className="text-slate-400">Related DocType</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 border-t-2 border-blue-400 border-dashed" />
            <span className="text-slate-400">Link Field</span>
          </div>
        </div>
      </div>
      
      {/* Instructions */}
      <div className="absolute top-4 left-4 p-2 bg-slate-800/90 rounded-lg border border-slate-700 text-xs text-slate-400">
        Drag from ● to ● to create a Link field
      </div>
    </div>
  );
}

export default ERDView;
