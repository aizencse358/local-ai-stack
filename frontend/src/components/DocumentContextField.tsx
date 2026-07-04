interface DocumentContextFieldProps {
  value: string
  onChange: (value: string) => void
}

export function DocumentContextField({ value, onChange }: DocumentContextFieldProps) {
  const wordCount = value.trim() ? value.trim().split(/\s+/).length : 0

  return (
    <details className="document-context">
      <summary>
        Document context (optional){wordCount > 0 && ` — ${wordCount} words`}
      </summary>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Paste document text here. The assistant will answer questions using it."
        rows={6}
      />
    </details>
  )
}
