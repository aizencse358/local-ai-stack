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
          </div>
        )
      })}
      <div ref={bottomRef} />
    </div>
  )
}
