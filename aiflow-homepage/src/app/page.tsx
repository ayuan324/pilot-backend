"use client"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import StarryBackground from "@/components/StarryBackground"
import WorkflowPanel from "@/components/WorkflowPanel"
import {
  LinkIcon,
  Sparkles,
  Send,
  Rocket,
  Zap,
  AlertCircle
} from "lucide-react"
import { useState, useEffect } from "react"
import { useAPI, testConnection, Workflow } from "@/lib/api"

export default function Home() {
  const [prompt, setPrompt] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [showWorkflowPanel, setShowWorkflowPanel] = useState(false)
  const [generatedWorkflow, setGeneratedWorkflow] = useState<Workflow | null>(null)
  const [analysisData, setAnalysisData] = useState<any>(null)
  const [backendStatus, setBackendStatus] = useState<'unknown' | 'connected' | 'disconnected'>('unknown')
  const [error, setError] = useState<string | null>(null)

  const api = useAPI()

  // Check backend connection on mount
  useEffect(() => {
    const checkBackend = async () => {
      const isConnected = await testConnection()
      setBackendStatus(isConnected ? 'connected' : 'disconnected')
    }
    checkBackend()
  }, [])

  const handleSubmit = async () => {
    if (!prompt.trim()) return

    setIsGenerating(true)
    setError(null)

    try {
      // First analyze the prompt
      console.log("🔍 Analyzing prompt:", prompt)
      const analysis = await api.analyzePrompt(prompt)
      console.log("📊 Analysis result:", analysis)
      setAnalysisData(analysis.analysis)

      // Then generate the workflow
      console.log("🚀 Generating workflow...")
      const workflowResult = await api.generateWorkflow(prompt)
      console.log("✅ Workflow generated:", workflowResult)

      setGeneratedWorkflow(workflowResult.workflow)
      setShowWorkflowPanel(true)

    } catch (error: any) {
      console.error("❌ Generation failed:", error)
      setError(error.message || "Failed to generate workflow")
    } finally {
      setIsGenerating(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleExampleClick = async (examplePrompt: string) => {
    setPrompt(examplePrompt)
    await new Promise(resolve => setTimeout(resolve, 100)) // Brief delay for UX
    handleSubmit()
  }

  const handleWorkflowSave = (workflow: Workflow) => {
    console.log("💾 Saving workflow:", workflow)
    // TODO: Implement save to backend when auth is added
  }

  const handleWorkflowExecute = (workflow: Workflow) => {
    console.log("▶️ Executing workflow:", workflow)
    // TODO: Implement real execution
  }

  return (
    <div className="flex flex-col h-full w-full bg-gray-950 relative overflow-hidden">
      {/* Enhanced Background with Starry Effect */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Main gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-gray-950 to-slate-900" />

        {/* Radial gradient overlay */}
        <div className="absolute inset-0 bg-gradient-radial from-transparent via-blue-950/3 to-gray-950/80" />
      </div>

      {/* Starry Background */}
      <StarryBackground />

      {/* Header */}
      <header className="flex shrink-0 select-none items-center bg-gray-950/80 backdrop-blur-sm px-3 md:px-5 py-4 border-b border-gray-800/50 relative z-10">
        <div className="flex grow-1 basis-40 md:basis-60 items-center gap-2 text-white">
          <Link href="/" className="text-xl md:text-2xl font-semibold text-blue-400 flex items-center">
            <Rocket className="w-6 h-6 md:w-8 md:h-8 mr-1 md:mr-2 text-blue-400" />
            <span className="hidden sm:block">πlot</span>
          </Link>
        </div>
        <div className="flex-1 select-text px-2 md:px-4 text-sm text-center text-gray-300">
          {/* Backend Status Indicator */}
          {backendStatus === 'connected' && (
            <div className="flex items-center justify-center gap-2 text-green-400">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-xs">Backend Connected</span>
            </div>
          )}
          {backendStatus === 'disconnected' && (
            <div className="flex items-center justify-center gap-2 text-yellow-400">
              <AlertCircle className="w-3 h-3" />
              <span className="text-xs">Backend Offline</span>
            </div>
          )}
        </div>
        <div className="flex grow-1 basis-40 md:basis-60 justify-end items-center gap-1.5 md:gap-2.5">
          <div className="flex items-center gap-1 md:gap-1.5">
            <Button variant="secondary" size="sm" className="bg-gray-800 text-gray-200 hover:bg-gray-700 text-xs md:text-sm px-2 md:px-3">
              Sign In
            </Button>
            <Button size="sm" className="bg-blue-600 text-white hover:bg-blue-700 text-xs md:text-sm px-2 md:px-3">
              Get Started
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="relative flex h-full w-full overflow-hidden">
        <div className="flex overflow-auto size-full flex-col relative z-10">

          {/* Hero Section */}
          <div className="flex flex-col mt-[12vh] md:mt-[18vh] mx-4 md:mx-8">
            <h1 className="text-2xl sm:text-3xl md:text-[44px] text-center font-semibold text-white tracking-tight mb-4 md:mb-6 leading-tight">
              What AI workflow do you want to build?
            </h1>
            <p className="mb-4 md:mb-6 text-center text-gray-400 text-sm md:text-base px-4">
              <span>Design, create, and deploy intelligent AI workflows with </span>
              <span className="text-white font-medium">natural language</span> and <span className="text-white font-medium">visual tools</span>.
            </p>
          </div>

          {/* Enhanced Prompt Input */}
          <div className="relative px-4 md:px-8 w-full max-w-2xl mx-auto">
            <div className="relative shadow-2xl border border-gray-700/50 bg-gray-900/60 backdrop-blur-md rounded-lg overflow-hidden">
              {/* Input glow effect with rotating animation when generating */}
              <div className="absolute inset-0 rounded-lg">
                {!isGenerating ? (
                  <>
                    {/* Static glow when not generating */}
                    <div className="absolute top-0 left-[10px] h-px w-[120px] bg-gradient-to-r from-blue-300/0 via-blue-300 to-blue-300/0 mix-blend-overlay" />
                    <div className="absolute top-0 left-[15px] h-px w-[80px] bg-gradient-to-r from-cyan-400/0 via-cyan-400/90 to-cyan-400/0" />
                  </>
                ) : (
                  /* Rotating glow when generating */
                  <div className="absolute inset-0 animate-spin" style={{ animationDuration: '3s' }}>
                    <div className="absolute top-0 left-[10px] h-px w-[120px] bg-gradient-to-r from-blue-300/0 via-blue-300 to-blue-300/0 mix-blend-overlay" />
                    <div className="absolute top-0 left-[15px] h-px w-[80px] bg-gradient-to-r from-cyan-400/0 via-cyan-400/90 to-cyan-400/0" />
                  </div>
                )}
              </div>
              <div className="relative">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="w-full pl-4 pt-4 pr-20 bg-transparent border-0 text-white placeholder-gray-500 text-sm resize-none focus:ring-0 focus:outline-none focus-visible:ring-0 focus-visible:outline-none"
                  placeholder="Describe your AI workflow idea..."
                  disabled={isGenerating}
                  style={{
                    minHeight: '76px',
                    maxHeight: '200px',
                    height: '76px',
                    lineHeight: '1.5'
                  }}
                />
                {prompt.trim() && (
                  <Button
                    onClick={handleSubmit}
                    disabled={isGenerating || backendStatus === 'disconnected'}
                    className="absolute bottom-3 right-3 bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-md disabled:opacity-50"
                    size="sm"
                  >
                    {isGenerating ? (
                      <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                    ) : (
                      <Zap className="w-4 h-4" />
                    )}
                  </Button>
                )}
              </div>
              <div className="flex justify-between text-sm px-4 pb-4 pt-2 min-h-[40px]">
                <div className="flex gap-1 items-center">
                  <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-gray-800 p-1">
                    <LinkIcon className="w-5 h-5" />
                  </Button>
                  <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-gray-800 p-1 opacity-30" disabled>
                    <Sparkles className="w-5 h-5" />
                  </Button>
                </div>
                <div className="text-xs text-gray-500 flex items-center">
                  {prompt.trim() ? `${prompt.length} characters` : (
                    backendStatus === 'connected' ? "Press Enter to generate" : "Backend offline"
                  )}
                </div>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                <div className="flex items-center gap-2 text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4" />
                  {error}
                </div>
              </div>
            )}
          </div>

          {/* Example Prompts */}
          <div className="flex flex-wrap items-center justify-center gap-2 mx-4 md:mx-10 mt-6">
            <Button
              variant="outline"
              size="sm"
              className="border-gray-700/50 bg-gray-800/50 text-gray-300 hover:bg-gray-700 hover:text-white rounded-full backdrop-blur-sm"
              onClick={() => handleExampleClick("Build a customer support chatbot")}
              disabled={isGenerating}
            >
              Build a customer support chatbot
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="border-gray-700/50 bg-gray-800/50 text-gray-300 hover:bg-gray-700 hover:text-white rounded-full backdrop-blur-sm"
              onClick={() => handleExampleClick("Create a content generation pipeline")}
              disabled={isGenerating}
            >
              Create a content generation pipeline
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="border-gray-700/50 bg-gray-800/50 text-gray-300 hover:bg-gray-700 hover:text-white rounded-full backdrop-blur-sm"
              onClick={() => handleExampleClick("Design a data analysis workflow")}
              disabled={isGenerating}
            >
              Design a data analysis workflow
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="border-gray-700/50 bg-gray-800/50 text-gray-300 hover:bg-gray-700 hover:text-white rounded-full backdrop-blur-sm"
              onClick={() => handleExampleClick("Build an AI research assistant")}
              disabled={isGenerating}
            >
              Build an AI research assistant
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="border-gray-700/50 bg-gray-800/50 text-gray-300 hover:bg-gray-700 hover:text-white rounded-full backdrop-blur-sm"
              onClick={() => handleExampleClick("Create automated workflows")}
              disabled={isGenerating}
            >
              Create automated workflows
            </Button>
          </div>

          {/* Template Showcase */}
          <div className="flex flex-col items-center mt-6">
            <span className="text-gray-500 text-sm mx-4 md:mx-10 mb-5">or start with a template</span>
            <div className="grid grid-cols-4 md:grid-cols-7 mx-4 md:mx-10 gap-3 md:gap-4 justify-items-center">
              <div className="text-2xl md:text-4xl opacity-30 hover:opacity-75 transition-opacity cursor-pointer">🤖</div>
              <div className="text-2xl md:text-4xl opacity-25 hover:opacity-65 transition-opacity cursor-pointer">📊</div>
              <div className="text-2xl md:text-4xl opacity-25 hover:opacity-65 transition-opacity cursor-pointer">💬</div>
              <div className="text-2xl md:text-4xl opacity-25 hover:opacity-75 transition-opacity cursor-pointer">🔍</div>
              <div className="text-2xl md:text-4xl opacity-25 hover:opacity-75 transition-opacity cursor-pointer md:block">📝</div>
              <div className="text-2xl md:text-4xl opacity-25 hover:opacity-65 transition-opacity cursor-pointer hidden md:block">🎯</div>
              <div className="text-2xl md:text-4xl opacity-25 hover:opacity-55 transition-opacity cursor-pointer hidden md:block">⚡</div>
            </div>
            <div className="grid grid-cols-4 md:grid-cols-7 mx-4 md:mx-10 mt-3 md:mt-5 gap-3 md:gap-4 justify-items-center">
              <div className="text-2xl md:text-4xl opacity-30 hover:opacity-80 transition-opacity cursor-pointer">🧠</div>
              <div className="text-2xl md:text-4xl opacity-25 hover:opacity-75 transition-opacity cursor-pointer">📈</div>
              <div className="text-2xl md:text-4xl opacity-25 hover:opacity-65 transition-opacity cursor-pointer">🔗</div>
              <div className="text-2xl md:text-4xl opacity-35 hover:opacity-80 transition-opacity cursor-pointer">🎨</div>
              <div className="text-2xl md:text-4xl opacity-25 hover:opacity-65 transition-opacity cursor-pointer md:block">📱</div>
              <div className="text-2xl md:text-4xl opacity-25 hover:opacity-65 transition-opacity cursor-pointer hidden md:block">🌐</div>
              <div className="text-2xl md:text-4xl opacity-25 hover:opacity-65 transition-opacity cursor-pointer hidden md:block">🔧</div>
            </div>
          </div>

          {/* Footer */}
          <footer className="flex flex-wrap gap-3.5 ml-auto pl-10 pb-2 pt-10 px-4 items-center justify-center text-sm text-gray-500 backdrop-blur-sm">
            <a href="/help" className="hover:text-gray-300 transition-colors">Help Center</a>
            <button className="bg-transparent hover:text-gray-300 transition-colors">Pricing</button>
            <a href="/terms" className="hover:text-gray-300 transition-colors">Terms</a>
            <a href="/privacy" className="hover:text-gray-300 transition-colors">Privacy</a>
            <div className="w-1 h-1 bg-gray-600 rounded-full" />
            <Link href="/" className="hover:text-gray-300 transition-colors">πlot</Link>
          </footer>
        </div>
      </div>

      {/* Workflow Panel */}
      <WorkflowPanel
        isVisible={showWorkflowPanel}
        onClose={() => setShowWorkflowPanel(false)}
        workflow={generatedWorkflow}
        analysisData={analysisData}
        onSave={handleWorkflowSave}
        onExecute={handleWorkflowExecute}
      />
    </div>
  )
}
