import { useState } from 'react'
import { useChat } from './useChat'
import { MessageList } from './components/MessageList'
import { ChatInput } from './components/ChatInput'
import { SystemPromptField } from './components/SystemPromptField'
import './App.css'

function App() {
  const { messages, sendMessage, isStreaming } = useChat()
  const [systemPrompt, setSystemPrompt] = useState('')

  return (
    <div className="app">
      <header className="app-header">
        <h1>Local AI Chat</h1>
        <p>Ollama + FastAPI + React, streaming token by token.</p>
      </header>

      <SystemPromptField value={systemPrompt} onChange={setSystemPrompt} />

      <MessageList messages={messages} isStreaming={isStreaming} />

      <ChatInput
        disabled={isStreaming}
        onSend={(content) => sendMessage(content, systemPrompt)}
      />
    </div>
  )
}

export default App
