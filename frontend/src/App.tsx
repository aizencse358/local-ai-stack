import { useState } from 'react'
import { useChat } from './useChat'
import { MessageList } from './components/MessageList'
import { ChatInput } from './components/ChatInput'
import { SystemPromptField } from './components/SystemPromptField'
import { DocumentContextField } from './components/DocumentContextField'
import { DocumentUpload } from './components/DocumentUpload'
import { SessionList } from './components/SessionList'
import './App.css'

function App() {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const { messages, sendMessage, isStreaming, loadSession, reset } = useChat(setCurrentSessionId)
  const [systemPrompt, setSystemPrompt] = useState('')
  const [documentContext, setDocumentContext] = useState('')
  const [ragEnabled, setRagEnabled] = useState(false)

  const handleNewChat = () => {
    setCurrentSessionId(null)
    reset()
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Local AI Chat</h1>
        <p>Ollama + FastAPI + React, streaming token by token.</p>
      </header>

      <SessionList
        currentSessionId={currentSessionId}
        isStreaming={isStreaming}
        onNewChat={handleNewChat}
        onLoadSession={(detail) => {
          setCurrentSessionId(detail.id)
          loadSession(detail)
        }}
      />
      <SystemPromptField value={systemPrompt} onChange={setSystemPrompt} />
      <DocumentContextField value={documentContext} onChange={setDocumentContext} />
      <DocumentUpload ragEnabled={ragEnabled} onRagToggle={setRagEnabled} />

      <MessageList messages={messages} isStreaming={isStreaming} />

      <ChatInput
        disabled={isStreaming}
        onSend={(content) =>
          sendMessage(content, {
            system: systemPrompt,
            context: documentContext,
            rag: ragEnabled,
            sessionId: currentSessionId,
          })
        }
      />
    </div>
  )
}

export default App
