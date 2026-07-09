import { useEffect, useState } from 'react'
import type { DocumentInfo } from '../types'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

interface DocumentUploadProps {
  ragEnabled: boolean
  onRagToggle: (enabled: boolean) => void
}

export function DocumentUpload({ ragEnabled, onRagToggle }: DocumentUploadProps) {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [status, setStatus] = useState('')

  const refresh = async () => {
    const response = await fetch(`${BACKEND_URL}/api/documents`)
    if (response.ok) {
      setDocuments(await response.json())
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return

    setStatus('Indexing…')
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${BACKEND_URL}/api/documents`, {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) {
        throw new Error(`Upload failed (${response.status})`)
      }
      const result = await response.json()
      setStatus(`Indexed ${result.chunk_count} chunks`)
      await refresh()
    } catch (err) {
      setStatus(err instanceof Error ? `Error: ${err.message}` : 'Upload failed')
    }
  }

  const handleDelete = async (id: string) => {
    await fetch(`${BACKEND_URL}/api/documents/${id}`, { method: 'DELETE' })
    await refresh()
  }

  return (
    <details className="document-upload">
      <summary>Uploaded documents (RAG){documents.length > 0 && ` — ${documents.length}`}</summary>

      <label className="rag-toggle">
        <input
          type="checkbox"
          checked={ragEnabled}
          onChange={(e) => onRagToggle(e.target.checked)}
        />
        Use uploaded documents to answer
      </label>

      <input type="file" accept=".txt,.md,.pdf,.docx" onChange={handleUpload} />
      {status && <p className="upload-status">{status}</p>}

      <ul className="document-list">
        {documents.map((doc) => (
          <li key={doc.id}>
            {doc.filename} ({doc.chunk_count} chunks)
            <button type="button" onClick={() => handleDelete(doc.id)} aria-label={`Remove ${doc.filename}`}>
              ×
            </button>
          </li>
        ))}
      </ul>
    </details>
  )
}
