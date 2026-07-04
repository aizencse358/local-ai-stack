interface SystemPromptFieldProps {
  value: string
  onChange: (value: string) => void
}

export function SystemPromptField({ value, onChange }: SystemPromptFieldProps) {
  return (
    <details className="system-prompt">
      <summary>System prompt (optional)</summary>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="e.g. You are a helpful assistant who answers concisely."
        rows={3}
      />
    </details>
  )
}
