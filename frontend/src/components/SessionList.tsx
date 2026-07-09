import { useEffect, useState } from 'react'
import type { SessionInfo, SessionDetail } from '../types'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

interface SessionListProps {
  currentSessionId: string | null
  isStreaming: boolean
  onNewChat: () => void
  onLoadSession: (detail: SessionDetail) => void
}

export function SessionList({
  currentSessionId,
  isStreaming,
  onNewChat,
  onLoadSession,
}: SessionListProps) {
  const [sessions, setSessions] = useState<SessionInfo[]>([])

  const refresh = async () => {
    const response = await fetch(`${BACKEND_URL}/api/sessions`)
    if (response.ok) {
      setSessions(await response.json())
    }
  }

  useEffect(() => {
    if (!isStreaming) {
      refresh()
    }
  }, [isStreaming])

  const handleOpen = async (id: string) => {
    const response = await fetch(`${BACKEND_URL}/api/sessions/${id}`)
    if (response.ok) {
      onLoadSession(await response.json())
    }
  }

  const handleDelete = async (id: string) => {
    await fetch(`${BACKEND_URL}/api/sessions/${id}`, { method: 'DELETE' })
    if (id === currentSessionId) {
      onNewChat()
    }
    await refresh()
  }

  return (
    <details className="session-list" open>
      <summary>Conversations{sessions.length > 0 && ` — ${sessions.length}`}</summary>

      <button type="button" className="new-chat-button" onClick={onNewChat}>
        + New Chat
      </button>

      <ul>
        {sessions.map((session) => (
          <li key={session.id} className={session.id === currentSessionId ? 'active' : ''}>
            <button type="button" onClick={() => handleOpen(session.id)}>
              {session.title}
            </button>
            <button
              type="button"
              className="delete-button"
              onClick={() => handleDelete(session.id)}
              aria-label={`Delete ${session.title}`}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </details>
  )
}
