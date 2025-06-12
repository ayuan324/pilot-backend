"use client"

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, Play, Save, Settings, Info, Zap, Clock, DollarSign } from "lucide-react"

import WorkflowEditor from './WorkflowEditor'
import { Workflow, WorkflowNode, WorkflowEdge } from '@/lib/api'

interface WorkflowPanelProps {
  isVisible: boolean
  onClose: () => void
  workflow?: Workflow
  analysisData?: {
    intent: string
    complexity: string
    confidence: number
  }
  onSave?: (workflow: Workflow) => void
  onExecute?: (workflow: Workflow) => void
}

interface ExecutionStatus {
  status: 'idle' | 'running' | 'completed' | 'error'
  progress: number
  currentNode?: string
  logs: string[]
  result?: any
}

export default function WorkflowPanel({
  isVisible,
  onClose,
  workflow,
  analysisData,
  onSave,
  onExecute
}: WorkflowPanelProps) {
  const [currentWorkflow, setCurrentWorkflow] = useState<Workflow | null>(workflow || null)
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus>({
    status: 'idle',
    progress: 0,
    logs: []
  })
  const [selectedTab, setSelectedTab] = useState('editor')

  useEffect(() => {
    if (workflow) {
      setCurrentWorkflow(workflow)
    }
  }, [workflow])

  const handleWorkflowSave = (workflowData: any) => {
    if (currentWorkflow) {
      const updatedWorkflow = {
        ...currentWorkflow,
        nodes: workflowData.nodes,
        edges: workflowData.edges
      }
      setCurrentWorkflow(updatedWorkflow)
      onSave?.(updatedWorkflow)
    }
  }

  const handleWorkflowExecute = async (workflowData: any) => {
    if (!currentWorkflow) return

    setExecutionStatus({
      status: 'running',
      progress: 0,
      logs: ['🚀 Starting workflow execution...']
    })

    // Simulate execution for demo
    try {
      setSelectedTab('execution')

      // Simulate progress updates
      const nodes = workflowData.nodes
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i]
        const progress = (i + 1) / nodes.length

        setExecutionStatus(prev => ({
          ...prev,
          progress,
          currentNode: node.id,
          logs: [...prev.logs, `⚙️ Executing ${node.config.name || node.type} node...`]
        }))

        // Simulate node execution time
        await new Promise(resolve => setTimeout(resolve, 1000))

        setExecutionStatus(prev => ({
          ...prev,
          logs: [...prev.logs, `✅ ${node.config.name || node.type} completed`]
        }))
      }

      setExecutionStatus(prev => ({
        ...prev,
        status: 'completed',
        progress: 1,
        result: { message: 'Workflow executed successfully!', output: 'Generated result...' },
        logs: [...prev.logs, '🎉 Workflow execution completed!']
      }))

      onExecute?.(currentWorkflow)
    } catch (error) {
      setExecutionStatus(prev => ({
        ...prev,
        status: 'error',
        logs: [...prev.logs, `❌ Execution failed: ${error}`]
      }))
    }
  }

  if (!isVisible) return null

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="absolute inset-x-0 top-0 h-full bg-white transform transition-transform duration-300 ease-in-out">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-white sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-gray-900">
              {currentWorkflow?.name || 'AI Workflow Editor'}
            </h2>
            {analysisData && (
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="capitalize">
                  {analysisData.intent}
                </Badge>
                <Badge variant={analysisData.complexity === 'simple' ? 'default' : 'secondary'}>
                  {analysisData.complexity}
                </Badge>
                <span className="text-sm text-gray-500">
                  {Math.round(analysisData.confidence * 100)}% confidence
                </span>
              </div>
            )}
          </div>
          <Button variant="ghost" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Main Content */}
        <div className="flex h-[calc(100vh-80px)]">
          {/* Editor Area */}
          <div className="flex-1 relative">
            <Tabs value={selectedTab} onValueChange={setSelectedTab} className="h-full">
              <TabsList className="absolute top-4 left-4 z-10 bg-white shadow-sm">
                <TabsTrigger value="editor">Editor</TabsTrigger>
                <TabsTrigger value="execution">Execution</TabsTrigger>
                <TabsTrigger value="settings">Settings</TabsTrigger>
              </TabsList>

              <TabsContent value="editor" className="h-full m-0">
                {currentWorkflow && (
                  <WorkflowEditor
                    onSave={handleWorkflowSave}
                    onExecute={handleWorkflowExecute}
                    className="h-full"
                  />
                )}
              </TabsContent>

              <TabsContent value="execution" className="h-full m-0 p-4">
                <ExecutionPanel executionStatus={executionStatus} />
              </TabsContent>

              <TabsContent value="settings" className="h-full m-0 p-4">
                <SettingsPanel workflow={currentWorkflow} />
              </TabsContent>
            </Tabs>
          </div>

          {/* Side Panel */}
          <div className="w-80 border-l bg-gray-50 p-4 overflow-y-auto">
            <WorkflowInfo workflow={currentWorkflow} analysisData={analysisData} />
          </div>
        </div>
      </div>
    </div>
  )
}

// Execution Panel Component
function ExecutionPanel({ executionStatus }: { executionStatus: ExecutionStatus }) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="w-5 h-5" />
            Execution Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Status:</span>
              <Badge
                variant={
                  executionStatus.status === 'running' ? 'default' :
                  executionStatus.status === 'completed' ? 'default' :
                  executionStatus.status === 'error' ? 'destructive' : 'secondary'
                }
              >
                {executionStatus.status}
              </Badge>
            </div>

            {executionStatus.status === 'running' && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Progress:</span>
                  <span className="text-sm font-medium">
                    {Math.round(executionStatus.progress * 100)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${executionStatus.progress * 100}%` }}
                  />
                </div>
              </div>
            )}

            {executionStatus.currentNode && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Current Node:</span>
                <Badge variant="outline">{executionStatus.currentNode}</Badge>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Execution Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Execution Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-64">
            <div className="space-y-1">
              {executionStatus.logs.map((log, index) => (
                <div key={index} className="text-sm font-mono text-gray-700 p-2 bg-gray-100 rounded">
                  {log}
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Execution Result */}
      {executionStatus.result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Result</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-sm text-green-700 font-medium">
                {executionStatus.result.message}
              </p>
              {executionStatus.result.output && (
                <div className="p-3 bg-green-50 rounded border">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                    {executionStatus.result.output}
                  </pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Settings Panel Component
function SettingsPanel({ workflow }: { workflow: Workflow | null }) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Workflow Settings
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Name</label>
              <p className="text-sm text-gray-600 mt-1">{workflow?.name || 'Untitled Workflow'}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Description</label>
              <p className="text-sm text-gray-600 mt-1">{workflow?.description || 'No description'}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Nodes</label>
              <p className="text-sm text-gray-600 mt-1">{workflow?.nodes?.length || 0} nodes</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Connections</label>
              <p className="text-sm text-gray-600 mt-1">{workflow?.edges?.length || 0} connections</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Workflow Info Component
function WorkflowInfo({
  workflow,
  analysisData
}: {
  workflow: Workflow | null
  analysisData?: any
}) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Info className="w-4 h-4" />
            Workflow Info
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {analysisData && (
            <>
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Intent</span>
                <p className="text-sm capitalize">{analysisData.intent}</p>
              </div>
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Complexity</span>
                <p className="text-sm capitalize">{analysisData.complexity}</p>
              </div>
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Confidence</span>
                <p className="text-sm">{Math.round(analysisData.confidence * 100)}%</p>
              </div>
            </>
          )}

          {workflow && (
            <>
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Nodes</span>
                <p className="text-sm">{workflow.nodes?.length || 0}</p>
              </div>
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Connections</span>
                <p className="text-sm">{workflow.edges?.length || 0}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Zap className="w-4 h-4" />
            Estimated Metrics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-600">~2-5 seconds</span>
          </div>
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-600">$0.001-0.01</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
