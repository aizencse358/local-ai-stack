export type Role = 'system' | 'user' | 'assistant'

export interface RetrievedChunk {
  filename: string
  text: string
  score: number
}

export interface ChatMessage {
  role: Role
  content: string
  sources?: RetrievedChunk[]
}

export interface DocumentInfo {
  id: string
  filename: string
  chunk_count: number
}
