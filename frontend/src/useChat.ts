import { useCallback, useRef, useState } from 'react'
import type { ChatMessage, RetrievedChunk } from './types'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    async (content: string, options?: { system?: string; context?: string; rag?: boolean }) => {
      const userMessage: ChatMessage = { role: 'user', content }
      const history = [...messages, userMessage]
      setMessages([...history, { role: 'assistant', content: '' }])
      setIsStreaming(true)

      const controller = new AbortController()
      abortRef.current = controller

      try {
        const response = await fetch(`${BACKEND_URL}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: history,
            system: options?.system || undefined,
            context: options?.context || undefined,
            rag: options?.rag || undefined,
          }),
          signal: controller.signal,
        })

        if (!response.body) {
          throw new Error('Response body is empty')
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let streamDone = false

        while (!streamDone) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const payload = line.slice('data: '.length)
            if (payload === '[DONE]') {
              // Stop on the application-level sentinel rather than waiting for
              // the transport stream to close, which can lag behind or never
              // resolve depending on proxy/keep-alive behavior.
              streamDone = true
              break
            }

            const parsed = JSON.parse(payload) as { token?: string; sources?: RetrievedChunk[] }

            if (parsed.sources) {
              setMessages((prev) => {
                const next = [...prev]
                const last = next[next.length - 1]
                next[next.length - 1] = { ...last, sources: parsed.sources }
                return next
              })
              continue
            }

            setMessages((prev) => {
              const next = [...prev]
              const last = next[next.length - 1]
              next[next.length - 1] = { ...last, content: last.content + (parsed.token ?? '') }
              return next
            })
          }
        }

        await reader.cancel().catch(() => {})
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setMessages((prev) => {
            const next = [...prev]
            const last = next[next.length - 1]
            next[next.length - 1] = {
              ...last,
              content: last.content + `\n\n[error: ${err.message}]`,
            }
            return next
          })
        }
      } finally {
        setIsStreaming(false)
        abortRef.current = null
      }
    },
    [messages],
  )

  const stop = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { messages, sendMessage, isStreaming, stop }
}
