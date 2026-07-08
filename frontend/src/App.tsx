import { useState } from 'react'
import { useChat } from './useChat'
import { MessageList } from './components/MessageList'
import { ChatInput } from './components/ChatInput'
import { SystemPromptField } from './components/SystemPromptField'
import { DocumentContextField } from './components/DocumentContextField'
import { DocumentUpload } from './components/DocumentUpload'
import './App.css'

function App() {
  const { messages, sendMessage, isStreaming } = useChat()
  const [systemPrompt, setSystemPrompt] = useState('')
  const [documentContext, setDocumentContext] = useState('')
  const [ragEnabled, setRagEnabled] = useState(false)

  return (
    <div className="app">
      <header className="app-header">
        <h1>Local AI Chat</h1>
        <p>Ollama + FastAPI + React, streaming token by token.</p>
      </header>

      <SystemPromptField value={systemPrompt} onChange={setSystemPrompt} />
      <DocumentContextField value={documentContext} onChange={setDocumentContext} />
      <DocumentUpload ragEnabled={ragEnabled} onRagToggle={setRagEnabled} />

      <MessageList messages={messages} isStreaming={isStreaming} />

      <ChatInput
        disabled={isStreaming}
        onSend={(content) =>
          sendMessage(content, { system: systemPrompt, context: documentContext, rag: ragEnabled })
        }
      />
    </div>
  )
}

export default App
