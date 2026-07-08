import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../types'

interface MessageListProps {
  messages: ChatMessage[]
  isStreaming: boolean
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="message-list">
      {messages.length === 0 && (
        <p className="empty-state">Send a message to start chatting.</p>
      )}
      {messages.map((message, i) => {
        const isLast = i === messages.length - 1
        const isPending =
          isStreaming && isLast && message.role === 'assistant' && !message.content

        return (
          <div key={i} className={`message message-${message.role}`}>
            <span className="message-role">{message.role}</span>
            {isPending ? (
              <span className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </span>
            ) : (
              <p className="message-content">{message.content}</p>
            )}
            {message.sources && message.sources.length > 0 && (
              <details className="sources">
                <summary>Sources ({message.sources.length})</summary>
                <ul>
                  {message.sources.map((source, j) => (
                    <li key={j}>
                      <strong>{source.filename}</strong>
                      <p>{source.text}</p>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        )
      })}
      <div ref={bottomRef} />
    </div>
  )
}
