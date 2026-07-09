import { useEffect, useState } from 'react'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

interface ModelPickerProps {
  value: string
  onChange: (value: string) => void
}

export function ModelPicker({ value, onChange }: ModelPickerProps) {
  const [models, setModels] = useState<string[]>([])

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/models`)
      .then((response) => (response.ok ? response.json() : []))
      .then(setModels)
      .catch(() => setModels([]))
  }, [])

  return (
    <select
      className="model-picker"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label="Model"
    >
      <option value="">Server default</option>
      {models.map((model) => (
        <option key={model} value={model}>
          {model}
        </option>
      ))}
    </select>
  )
}
