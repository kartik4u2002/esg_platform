import React, { useCallback, useRef, useState } from 'react'

interface DragDropZoneProps {
  onFileSelect: (file: File) => void
  accept?: string
  label?: string
  disabled?: boolean
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const DragDropZone: React.FC<DragDropZoneProps> = ({
  onFileSelect,
  accept = '.csv',
  label = 'Drop your CSV file here',
  disabled = false,
}) => {
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDragIn = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (!disabled) setIsDragOver(true)
    },
    [disabled]
  )

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragOver(false)
      if (disabled) return

      const files = e.dataTransfer.files
      if (files && files.length > 0) {
        const file = files[0]
        setSelectedFile(file)
        onFileSelect(file)
      }
    },
    [onFileSelect, disabled]
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files && files.length > 0) {
        const file = files[0]
        setSelectedFile(file)
        onFileSelect(file)
      }
    },
    [onFileSelect]
  )

  const handleClick = useCallback(() => {
    if (!disabled) fileInputRef.current?.click()
  }, [disabled])

  return (
    <div
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`relative group cursor-pointer rounded-xl border-2 border-dashed transition-all duration-300 p-8 text-center
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${
          isDragOver
            ? 'border-primary-400 bg-primary-500/10 scale-[1.01]'
            : 'border-slate-600/50 hover:border-slate-500/70 hover:bg-white/[0.02]'
        }
      `}
    >
      {/* Gradient border on drag over */}
      {isDragOver && (
        <div className="absolute inset-0 rounded-xl gradient-border pointer-events-none" />
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileInput}
        className="hidden"
        disabled={disabled}
      />

      {selectedFile ? (
        <div className="flex flex-col items-center gap-2">
          {/* File icon */}
          <svg
            className="w-10 h-10 text-primary-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
            />
          </svg>
          <p className="text-sm font-medium text-slate-200">{selectedFile.name}</p>
          <p className="text-xs text-slate-500">{formatFileSize(selectedFile.size)}</p>
          <button
            onClick={(e) => {
              e.stopPropagation()
              setSelectedFile(null)
              if (fileInputRef.current) fileInputRef.current.value = ''
            }}
            className="text-xs text-slate-500 hover:text-slate-300 underline transition-colors mt-1"
          >
            Choose a different file
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          {/* Upload icon */}
          <svg
            className="w-10 h-10 text-slate-500 group-hover:text-slate-400 transition-colors"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="text-xs text-slate-600">or click to browse</p>
        </div>
      )}
    </div>
  )
}

export default DragDropZone
