/**
 * πlot API Client
 * Handles communication with the FastAPI backend
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios'

// API Configuration - 使用环境变量，生产环境回退到Railway URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://pilot-backend-production.up.railway.app'

// Types
export interface PromptAnalysisRequest {
  prompt: string
  context?: Record<string, any>
}

export interface PromptAnalysisResponse {
  success: boolean
  analysis: {
    intent: string
    complexity: 'simple' | 'medium' | 'complex'
    entities: string[]
    suggested_workflow: {
      name: string
      description: string
      estimated_nodes: number
      node_types: string[]
    }
    confidence: number
  }
}

export interface WorkflowGenerationRequest {
  prompt: string
  preferences?: Record<string, any>
}

export interface WorkflowNode {
  id: string
  type: string
  position: { x: number; y: number }
  config: Record<string, any>
}

export interface WorkflowEdge {
  source: string
  target: string
}

export interface Workflow {
  id: string
  name: string
  description: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  variables?: Array<{
    name: string
    type: string
    is_input?: boolean
    is_output?: boolean
  }>
}

export interface WorkflowGenerationResponse {
  success: boolean
  workflow: Workflow
  generation_meta: {
    model: string
    generated_at: string
  }
}

export interface WorkflowTemplate {
  id: string
  name: string
  description: string
  category: string
  difficulty: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
}

export interface TemplatesResponse {
  templates: WorkflowTemplate[]
  count: number
}

export interface AIModel {
  id: string
  name: string
  provider: string
  cost_per_1k_tokens: number
}

export interface ModelsResponse {
  success: boolean
  models: AIModel[]
}

// API Client Class
class PilotAPIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor for auth
    this.client.interceptors.request.use((config) => {
      // Add auth token if available (Clerk integration)
      const token = this.getAuthToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message)
        return Promise.reject(error)
      }
    )
  }

  private getAuthToken(): string | null {
    // TODO: Integrate with Clerk auth
    // For now, return null - we'll add auth later
    return null
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await this.client.get('/health')
    return response.data
  }

  // AI Services
  async analyzePrompt(request: PromptAnalysisRequest): Promise<PromptAnalysisResponse> {
    const response = await this.client.post('/api/v1/ai/analyze-prompt', request)
    return response.data
  }

  async generateWorkflow(request: WorkflowGenerationRequest): Promise<WorkflowGenerationResponse> {
    const response = await this.client.post('/api/v1/ai/generate-workflow', request)
    return response.data
  }

  async getAvailableModels(): Promise<ModelsResponse> {
    const response = await this.client.get('/api/v1/ai/models')
    return response.data
  }

  // Workflow Templates
  async getWorkflowTemplates(): Promise<TemplatesResponse> {
    const response = await this.client.get('/api/v1/workflows/templates')
    return response.data
  }

  // Workflow Management (requires auth)
  async createWorkflow(workflow: Partial<Workflow>): Promise<Workflow> {
    const response = await this.client.post('/api/v1/workflows', workflow)
    return response.data
  }

  async getWorkflows(): Promise<Workflow[]> {
    const response = await this.client.get('/api/v1/workflows')
    return response.data
  }

  async getWorkflow(id: string): Promise<Workflow> {
    const response = await this.client.get(`/api/v1/workflows/${id}`)
    return response.data
  }

  async updateWorkflow(id: string, updates: Partial<Workflow>): Promise<Workflow> {
    const response = await this.client.put(`/api/v1/workflows/${id}`, updates)
    return response.data
  }

  async deleteWorkflow(id: string): Promise<void> {
    await this.client.delete(`/api/v1/workflows/${id}`)
  }

  async executeWorkflow(id: string, inputData: Record<string, any>): Promise<{ execution_id: string; status: string }> {
    const response = await this.client.post(`/api/v1/workflows/${id}/execute`, { input_data: inputData })
    return response.data
  }

  // WebSocket Connection
  createWebSocket(userId: string): WebSocket {
    const wsUrl = API_BASE_URL.replace('http', 'ws') + `/ws/${userId}`
    return new WebSocket(wsUrl)
  }
}

// Export singleton instance
export const apiClient = new PilotAPIClient()

// Error handling utilities
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

export const handleAPIError = (error: any): APIError => {
  if (error.response) {
    return new APIError(
      error.response.data?.detail || error.response.data?.message || 'API Error',
      error.response.status,
      error.response.data
    )
  } else if (error.request) {
    return new APIError('Network Error: Unable to reach server')
  } else {
    return new APIError(error.message || 'Unknown API Error')
  }
}

// React hooks for API calls
export const useAPI = () => {
  const analyzePrompt = async (prompt: string) => {
    try {
      return await apiClient.analyzePrompt({ prompt })
    } catch (error) {
      throw handleAPIError(error)
    }
  }

  const generateWorkflow = async (prompt: string) => {
    try {
      return await apiClient.generateWorkflow({ prompt })
    } catch (error) {
      throw handleAPIError(error)
    }
  }

  const getTemplates = async () => {
    try {
      return await apiClient.getWorkflowTemplates()
    } catch (error) {
      throw handleAPIError(error)
    }
  }

  return {
    analyzePrompt,
    generateWorkflow,
    getTemplates,
    healthCheck: () => apiClient.healthCheck(),
    getModels: () => apiClient.getAvailableModels(),
  }
}

// Test connection utility
export const testConnection = async (): Promise<boolean> => {
  try {
    await apiClient.healthCheck()
    return true
  } catch (error) {
    console.error('Backend connection failed:', error)
    return false
  }
}
