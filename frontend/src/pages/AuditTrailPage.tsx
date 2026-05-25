import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getAuditRecords, getAuditTrail, exportAuditCSV } from '../api/endpoints'

const AuditTrailPage: React.FC = () => {
  const [page, setPage] = useState(1)
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(null)
  const [panelClosing, setPanelClosing] = useState(false)
  const pageSize = 20

  const { data, isLoading, isError } = useQuery({
    queryKey: ['auditRecords', page],
    queryFn: () => getAuditRecords({ page, page_size: pageSize }),
  })

  const records = data?.data?.results || data?.data || []
  const totalCount = data?.data?.count || records.length
  const totalPages = Math.ceil(totalCount / pageSize) || 1

  // Audit trail for selected record
  const { data: trailData, isLoading: trailLoading } = useQuery({
    queryKey: ['auditTrail', selectedRecordId],
    queryFn: () => getAuditTrail(selectedRecordId!),
    enabled: !!selectedRecordId,
  })

  const trailEvents = trailData?.data?.events || trailData?.data || []

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatTimestamp = (dateStr?: string) => {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const handleExportCSV = async () => {
    try {
      const response = await exportAuditCSV()
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `audit_export_${new Date().toISOString().split('T')[0]}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      // silently fail — user sees no download
    }
  }

  const closePanel = () => {
    setPanelClosing(true)
    setTimeout(() => {
      setSelectedRecordId(null)
      setPanelClosing(false)
    }, 300)
  }

  const openPanel = (id: string) => {
    setPanelClosing(false)
    setSelectedRecordId(id)
  }

  const actionBadge = (action: string) => {
    const map: Record<string, string> = {
      created: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
      approved: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
      rejected: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
      updated: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
      locked: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
    }
    return map[action.toLowerCase()] || 'bg-slate-500/15 text-slate-400 border-slate-500/30'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Audit Trail</h1>
          <p className="text-sm text-slate-500 mt-1">Approved and locked records with full audit history</p>
        </div>
        <button onClick={handleExportCSV} className="btn-primary flex items-center gap-2 text-sm">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Export CSV
        </button>
      </div>

      <div className="glass-card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <svg className="animate-spin w-8 h-8 text-primary-400" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : isError ? (
          <div className="text-center py-20 text-red-400">
            <p className="text-lg font-medium">Failed to load audit records</p>
          </div>
        ) : records.length === 0 ? (
          <div className="text-center py-20 text-slate-500">
            <svg className="w-12 h-12 mx-auto mb-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-lg font-medium">No audit records yet</p>
            <p className="text-sm mt-1">Records will appear here after approval.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Source</th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Facility</th>
                    <th className="text-right px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Quantity</th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Approved By</th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Locked At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/30">
                  {records.map((record: any, idx: number) => (
                    <tr
                      key={record.id}
                      onClick={() => openPanel(record.id)}
                      className={`cursor-pointer transition-colors duration-150 hover:bg-white/[0.03] ${
                        idx % 2 === 1 ? 'bg-white/[0.01]' : ''
                      } ${selectedRecordId === record.id ? 'bg-primary-500/[0.05]' : ''}`}
                    >
                      <td className="px-6 py-4 font-medium text-slate-200">
                        {record.source_type || record.source_name || '—'}
                      </td>
                      <td className="px-6 py-4 text-slate-300">
                        {record.facility_or_entity || record.facility_name || '—'}
                      </td>
                      <td className="px-6 py-4 text-right text-slate-300 tabular-nums font-mono">
                        {record.quantity_normalized != null
                          ? Number(record.quantity_normalized).toLocaleString()
                          : '—'}
                        {record.unit_normalized ? ` ${record.unit_normalized}` : ''}
                      </td>
                      <td className="px-6 py-4 text-slate-400">
                        {record.lock?.locked_by_name || record.approved_by || '—'}
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-xs whitespace-nowrap">
                        {formatDate(record.lock?.locked_at || record.locked_at || record.updated_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-slate-700/40">
                <p className="text-xs text-slate-500">
                  Page {page} of {totalPages} · {totalCount} records
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="btn-ghost text-xs px-3 py-1.5 disabled:opacity-30"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="btn-ghost text-xs px-3 py-1.5 disabled:opacity-30"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Slide-out Audit Trail Panel */}
      {selectedRecordId && (
        <>
          {/* Overlay */}
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 animate-fade-in"
            onClick={closePanel}
          />

          {/* Panel */}
          <div
            className={`fixed top-0 right-0 h-full w-full max-w-xl z-50 bg-surface-900 border-l border-slate-700/40 shadow-2xl shadow-black/40 flex flex-col ${
              panelClosing ? 'animate-slide-out-right' : 'animate-slide-in-right'
            }`}
          >
            {/* Panel header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-700/40">
              <h2 className="text-lg font-semibold text-slate-100">Audit Trail</h2>
              <button
                onClick={closePanel}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/10 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Panel content */}
            <div className="flex-1 overflow-y-auto px-6 py-6">
              {trailLoading ? (
                <div className="flex items-center justify-center py-20">
                  <svg className="animate-spin w-6 h-6 text-primary-400" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                </div>
              ) : trailEvents.length === 0 ? (
                <div className="text-center py-16 text-slate-500">
                  <p>No audit events found for this record.</p>
                </div>
              ) : (
                <div className="relative">
                  {/* Timeline line */}
                  <div className="absolute left-[11px] top-2 bottom-2 w-px bg-slate-700/50" />

                  <div className="space-y-6">
                    {[...trailEvents]
                      .sort(
                        (a: any, b: any) =>
                          new Date(b.timestamp || b.created_at).getTime() -
                          new Date(a.timestamp || a.created_at).getTime()
                      )
                      .map((event: any, idx: number) => (
                        <TrailEvent key={idx} event={event} actionBadge={actionBadge} formatTimestamp={formatTimestamp} />
                      ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// ─── TrailEvent sub-component ─────────────────────────────────────

interface TrailEventProps {
  event: any
  actionBadge: (action: string) => string
  formatTimestamp: (dateStr?: string) => string
}

const TrailEvent: React.FC<TrailEventProps> = ({ event, actionBadge, formatTimestamp }) => {
  const [showDiff, setShowDiff] = useState(false)

  const action = event.action || event.event_type || '—'
  const actor = event.actor_name || event.actor || event.performed_by || '—'
  const timestamp = event.occurred_at || event.timestamp || event.created_at
  const beforeState = event.before_state || event.old_state
  const afterState = event.after_state || event.new_state
  const hasDiff = beforeState || afterState

  return (
    <div className="relative pl-8">
      {/* Timeline dot */}
      <div className="absolute left-0 top-1.5 w-[23px] h-[23px] rounded-full bg-surface-900 border-2 border-slate-600 flex items-center justify-center">
        <div className="w-2 h-2 rounded-full bg-primary-400" />
      </div>

      <div className="glass-card p-4">
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${actionBadge(action)}`}
          >
            {action}
          </span>
          <span className="text-xs text-slate-400">by <span className="text-slate-300 font-medium">{actor}</span></span>
          <span className="text-xs text-slate-600 ml-auto">{formatTimestamp(timestamp)}</span>
        </div>

        {hasDiff && (
          <div>
            <button
              onClick={() => setShowDiff(!showDiff)}
              className="text-xs text-primary-400 hover:text-primary-300 transition-colors flex items-center gap-1 mt-1"
            >
              <svg
                className={`w-3.5 h-3.5 transition-transform ${showDiff ? 'rotate-90' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
              {showDiff ? 'Hide' : 'Show'} state diff
            </button>

            {showDiff && (
              <div className="mt-3 space-y-3 animate-fade-in">
                {beforeState && (
                  <div>
                    <span className="text-xs font-semibold text-red-400 uppercase tracking-wider">Before</span>
                    <pre className="mt-1 text-xs text-slate-400 bg-surface-950 rounded-lg p-3 overflow-auto max-h-48 font-mono">
                      {typeof beforeState === 'string'
                        ? beforeState
                        : JSON.stringify(beforeState, null, 2)}
                    </pre>
                  </div>
                )}
                {afterState && (
                  <div>
                    <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">After</span>
                    <pre className="mt-1 text-xs text-slate-400 bg-surface-950 rounded-lg p-3 overflow-auto max-h-48 font-mono">
                      {typeof afterState === 'string'
                        ? afterState
                        : JSON.stringify(afterState, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default AuditTrailPage
