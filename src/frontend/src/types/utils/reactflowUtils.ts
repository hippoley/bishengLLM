import { Node, Edge } from "@xyflow/react";
import { FlowType, NodeType } from "../flow";

export type cleanEdgesType = {
  flow: {
    edges: Edge[];
    nodes: NodeType[];
  };
  updateEdge: (edge: Edge[]) => void;
};

export type unselectAllNodesType = {
  updateNodes: (nodes: Node[]) => void;
  data: Node[];
};

export type updateEdgesHandleIdsType = {
  nodes: NodeType[];
  edges: Edge[];
};

export type generateFlowType = { newFlow: FlowType; removedEdges: Edge[] };

export type findLastNodeType = {
  nodes: NodeType[];
  edges: Edge[];
};
