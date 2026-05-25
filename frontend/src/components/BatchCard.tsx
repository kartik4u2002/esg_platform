import React from 'react'
import StatusPill from './StatusPill'

interface BatchCardProps {
  batch: {
    id: string
    source_name?: string
    file_name?: string
    status: string
    total_rows?: number
    processed_rows?: number
    created_at?: string
    updated_at?: string
    error_message?: string
  }
}

const BatchCard: React.FC<BatchCardProps> = ({ batch }) => {
  const progress =
    batch.total_rows && batch.total_rows > 0
      ? Math.round((( batch.processed_rows || 0) / batch.total_rows) * 100)
      : 0

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="glass-card p-4 mt-4 animate-slide-up">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          {batch.source_name && (
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">
              {batch.source_name}
            </p>
          )}
          {batch.file_name && (
            <p className="text-sm text-slate-300 truncate">{batch.file_name}</p>
          )}
        </div>
        <StatusPill status={batch.status} />
      </div>

      {/* Progress bar */}
      {batch.total_rows !== undefined && batch.total_rows > 0 && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
            <span>
              {batch.processed_rows || 0} / {batch.total_rows} rows
            </span>
            <span>{progress}%</span>
          </div>
          <div className="h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ease-out ${
                batch.status === 'failed'
                  ? 'bg-gradient-to-r from-red-500 to-rose-500'
                  : batch.status === 'completed'
                  ? 'bg-gradient-to-r from-emerald-500 to-green-400'
                  : 'bg-gradient-to-r from-primary-500 to-violet-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error message */}
      {batch.error_message && (
        <p className="text-xs text-red-400 bg-red-500/10 rounded-lg p-2 mb-3">
          {batch.error_message}
        </p>
      )}

      {/* Timestamps */}
      <div className="flex items-center gap-4 text-xs text-slate-600">
        <span>Created: {formatDate(batch.created_at)}</span>
        {batch.updated_at && <span>Updated: {formatDate(batch.updated_at)}</span>}
      </div>
    </div>
  )
}

export default BatchCard
