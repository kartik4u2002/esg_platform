import React from 'react'

interface StatusPillProps {
  status: string
  className?: string
}

const statusConfig: Record<string, { label: string; classes: string }> = {
  pending: {
    label: 'Pending',
    classes: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  },
  processing: {
    label: 'Processing',
    classes: 'bg-blue-500/15 text-blue-400 border-blue-500/30 animate-pulse-subtle',
  },
  completed: {
    label: 'Completed',
    classes: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  },
  failed: {
    label: 'Failed',
    classes: 'bg-red-500/15 text-red-400 border-red-500/30',
  },
  approved: {
    label: 'Approved',
    classes: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  },
  rejected: {
    label: 'Rejected',
    classes: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
  },
  review_pending: {
    label: 'Review Pending',
    classes: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
  },
}

const StatusPill: React.FC<StatusPillProps> = ({ status, className = '' }) => {
  const config = statusConfig[status] || {
    label: status.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
    classes: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full border ${config.classes} ${className}`}
    >
      {(status === 'processing') && (
        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
      )}
      {config.label}
    </span>
  )
}

export default StatusPill
