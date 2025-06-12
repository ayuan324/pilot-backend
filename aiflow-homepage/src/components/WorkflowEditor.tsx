"use client"

import React, { useCallback, useState, useMemo } from 'react'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  Panel,
  NodeTypes,
  EdgeTypes,
} from 'reactflow'
import 'reactflow/dist/style.css'

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Play, Save, Download, Settings, Plus, X } from "lucide-react"

// Custom Node Components
const StartNode = ({ data, selected }: any) => (
  <Card className={`min-w-[150px] ${selected ? 'ring-2 ring-blue-500' : ''} bg-green-50 border-green-200`}>
    <CardHeader className="pb-2">
      <CardTitle className="text-sm text-green-700 flex items-center gap-2">
        <div className="w-2 h-2 bg-green-500 rounded-full" />
        Start
      </CardTitle>
    </CardHeader>
    <CardContent className="pt-0">
      <p className="text-xs text-green-600">{data.name || 'Workflow Start'}</p>
    </CardContent>
  </Card>
)

const LLMNode = ({ data, selected }: any) => (
  <Card className={`min-w-[180px] ${selected ? 'ring-2 ring-blue-500' : ''} bg-blue-50 border-blue-200`}>
    <CardHeader className="pb-2">
      <CardTitle className="text-sm text-blue-700 flex items-center gap-2">
        <div className="w-2 h-2 bg-blue-500 rounded-full" />
        AI Model
      </CardTitle>
    </CardHeader>
    <CardContent className="pt-0">
      <p className="text-xs text-blue-600 font-medium">{data.name || 'LLM Processing'}</p>
      <Badge variant="secondary" className="text-xs mt-1">
        {data.model || 'gpt-3.5-turbo'}
      </Badge>
    </CardContent>
  </Card>
)

const ConditionNode = ({ data, selected }: any) => (
  <Card className={`min-w-[160px] ${selected ? 'ring-2 ring-blue-500' : ''} bg-yellow-50 border-yellow-200`}>
    <CardHeader className="pb-2">
      <CardTitle className="text-sm text-yellow-700 flex items-center gap-2">
        <div className="w-2 h-2 bg-yellow-500 rounded-full" />
        Condition
      </CardTitle>
    </CardHeader>
    <CardContent className="pt-0">
      <p className="text-xs text-yellow-600">{data.name || 'If/Then Logic'}</p>
    </CardContent>
  </Card>
)

const OutputNode = ({ data, selected }: any) => (
  <Card className={`min-w-[150px] ${selected ? 'ring-2 ring-blue-500' : ''} bg-purple-50 border-purple-200`}>
    <CardHeader className="pb-2">
      <CardTitle className="text-sm text-purple-700 flex items-center gap-2">
        <div className="w-2 h-2 bg-purple-500 rounded-full" />
        Output
      </CardTitle>
    </CardHeader>
    <CardContent className="pt-0">
      <p className="text-xs text-purple-600">{data.name || 'Final Result'}</p>
    </CardContent>
  </Card>
)

const CodeNode = ({ data, selected }: any) => (
  <Card className={`min-w-[160px] ${selected ? 'ring-2 ring-blue-500' : ''} bg-gray-50 border-gray-200`}>
    <CardHeader className="pb-2">
      <CardTitle className="text-sm text-gray-700 flex items-center gap-2">
        <div className="w-2 h-2 bg-gray-500 rounded-full" />
        Code
      </CardTitle>
    </CardHeader>
    <CardContent className="pt-0">
      <p className="text-xs text-gray-600">{data.name || 'Custom Code'}</p>
      <Badge variant="outline" className="text-xs mt-1">
        {data.language || 'python'}
      </Badge>
    </CardContent>
  </Card>
)

const HttpNode = ({ data, selected }: any) => (
  <Card className={`min-w-[160px] ${selected ? 'ring-2 ring-blue-500' : ''} bg-orange-50 border-orange-200`}>
    <CardHeader className="pb-2">
      <CardTitle className="text-sm text-orange-700 flex items-center gap-2">
        <div className="w-2 h-2 bg-orange-500 rounded-full" />
        HTTP
      </CardTitle>
    </CardHeader>
    <CardContent className="pt-0">
      <p className="text-xs text-orange-600">{data.name || 'API Request'}</p>
      <Badge variant="outline" className="text-xs mt-1">
        {data.method || 'GET'}
      </Badge>
    </CardContent>
  </Card>
)

// Node types mapping
const nodeTypes: NodeTypes = {
  start: StartNode,
  llm: LLMNode,
  condition: ConditionNode,
  output: OutputNode,
  code: CodeNode,
  http: HttpNode,
}

// Initial nodes for demo
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'start',
    position: { x: 100, y: 100 },
    data: { name: 'User Input' },
  },
  {
    id: '2',
    type: 'llm',
    position: { x: 300, y: 100 },
    data: { name: 'AI Processing', model: 'gpt-3.5-turbo' },
  },
  {
    id: '3',
    type: 'output',
    position: { x: 500, y: 100 },
    data: { name: 'Response' },
  },
]

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2' },
  { id: 'e2-3', source: '2', target: '3' },
]

interface WorkflowEditorProps {
  onSave?: (workflow: any) => void
  onExecute?: (workflow: any) => void
  className?: string
}

export default function WorkflowEditor({ onSave, onExecute, className }: WorkflowEditorProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [isExecuting, setIsExecuting] = useState(false)

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }, [])

  const addNode = useCallback((type: string) => {
    const newNode: Node = {
      id: `${nodes.length + 1}`,
      type,
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
      data: { name: `New ${type} Node` },
    }
    setNodes((nds) => [...nds, newNode])
  }, [nodes.length, setNodes])

  const deleteNode = useCallback((nodeId: string) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId))
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId))
    setSelectedNode(null)
  }, [setNodes, setEdges])

  const handleSave = useCallback(() => {
    const workflow = {
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.type,
        position: node.position,
        config: node.data
      })),
      edges: edges.map(edge => ({
        source: edge.source,
        target: edge.target
      }))
    }
    onSave?.(workflow)
  }, [nodes, edges, onSave])

  const handleExecute = useCallback(async () => {
    setIsExecuting(true)
    try {
      const workflow = {
        nodes: nodes.map(node => ({
          id: node.id,
          type: node.type,
          position: node.position,
          config: node.data
        })),
        edges: edges.map(edge => ({
          source: edge.source,
          target: edge.target
        }))
      }
      await onExecute?.(workflow)
    } finally {
      setIsExecuting(false)
    }
  }, [nodes, edges, onExecute])

  return (
    <div className={`h-full w-full relative bg-gray-50 ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        className="bg-gray-50"
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#e5e7eb" />
        <Controls className="bg-white border border-gray-200 rounded-lg shadow-sm" />

        {/* Top Panel */}
        <Panel position="top-left" className="flex gap-2 bg-white p-2 rounded-lg shadow-sm border border-gray-200">
          <Button
            onClick={handleSave}
            size="sm"
            variant="outline"
            className="flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            Save
          </Button>
          <Button
            onClick={handleExecute}
            size="sm"
            disabled={isExecuting}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
          >
            <Play className="w-4 h-4" />
            {isExecuting ? 'Running...' : 'Execute'}
          </Button>
        </Panel>

        {/* Node Palette */}
        <Panel position="top-right" className="bg-white p-3 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium mb-2 text-gray-700">Add Nodes</h3>
          <div className="flex flex-col gap-1">
            {[
              { type: 'start', label: 'Start', color: 'bg-green-100 text-green-700' },
              { type: 'llm', label: 'AI Model', color: 'bg-blue-100 text-blue-700' },
              { type: 'condition', label: 'Condition', color: 'bg-yellow-100 text-yellow-700' },
              { type: 'code', label: 'Code', color: 'bg-gray-100 text-gray-700' },
              { type: 'http', label: 'HTTP', color: 'bg-orange-100 text-orange-700' },
              { type: 'output', label: 'Output', color: 'bg-purple-100 text-purple-700' },
            ].map(({ type, label, color }) => (
              <Button
                key={type}
                onClick={() => addNode(type)}
                size="sm"
                variant="ghost"
                className={`justify-start ${color} hover:opacity-80`}
              >
                <Plus className="w-3 h-3 mr-1" />
                {label}
              </Button>
            ))}
          </div>
        </Panel>

        {/* Node Properties Panel */}
        {selectedNode && (
          <Panel position="bottom-right" className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 w-80">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-700">Node Properties</h3>
              <Button
                onClick={() => deleteNode(selectedNode.id)}
                size="sm"
                variant="ghost"
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-600">Type</label>
                <Badge variant="outline" className="ml-2">{selectedNode.type}</Badge>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600">Name</label>
                <p className="text-sm text-gray-800">{selectedNode.data.name || 'Unnamed'}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600">Position</label>
                <p className="text-sm text-gray-800">
                  x: {Math.round(selectedNode.position.x)}, y: {Math.round(selectedNode.position.y)}
                </p>
              </div>
              {selectedNode.type === 'llm' && selectedNode.data.model && (
                <div>
                  <label className="text-xs font-medium text-gray-600">Model</label>
                  <p className="text-sm text-gray-800">{selectedNode.data.model}</p>
                </div>
              )}
            </div>
            <Button
              size="sm"
              variant="outline"
              className="w-full mt-3 flex items-center gap-2"
            >
              <Settings className="w-3 h-3" />
              Configure
            </Button>
          </Panel>
        )}
      </ReactFlow>
    </div>
  )
}
