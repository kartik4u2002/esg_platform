import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { getReviewQueue } from '../api/endpoints'
import StatusPill from '../components/StatusPill'
import SeverityIcon from '../components/SeverityIcon'

const sourceTypes = [
  { value: '', label: 'All Sources' },
  { value: 'sap_procurement', label: 'SAP Procurement' },
  { value: 'utility_electricity', label: 'Utility Electricity' },
  { value: 'corporate_travel', label: 'Corporate Travel' },
]

const severityLevels = [
  { value: '', label: 'All Severities' },
  { value: 'error', label: 'Errors Only' },
  { value: 'warning', label: 'Warnings+' },
  { value: 'info', label: 'Info+' },
]

const scopeBadge: Record<string, { label: string; classes: string }> = {
  sap_procurement: { label: 'Scope 1', classes: 'bg-red-500/15 text-red-400 border-red-500/30' },
  utility_electricity: { label: 'Scope 2', classes: 'bg-amber-500/15 text-amber-400 border-amber-500/30' },
  corporate_travel: { label: 'Scope 3', classes: 'bg-teal-500/15 text-teal-400 border-teal-500/30' },
}

const ReviewQueuePage: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const batchFilter = searchParams.get('batch') || ''

  const [sourceType, setSourceType] = useState('')
  const [severity, setSeverity] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 20

  const params: Record<string, unknown> = {
    page,
    page_size: pageSize,
    review_status: 'pending',
  }
  if (sourceType) params.source_type = sourceType
  if (severity) params.severity = severity
  if (dateFrom) params.date_from = dateFrom
  if (dateTo) params.date_to = dateTo
  if (batchFilter) params.batch = batchFilter

  const { data, isLoading, isError } = useQuery({
    queryKey: ['reviewQueue', params],
    queryFn: () => getReviewQueue(params),
  })

  const records = data?.data?.results || data?.data || []
  const totalCount = data?.data?.count || records.length
  const totalPages = Math.ceil(totalCount / pageSize) || 1

  const clearFilters = () => {
    setSourceType('')
    setSeverity('')
    setDateFrom('')
    setDateTo('')
    setPage(1)
  }

  const hasActiveFilters = sourceType || severity || dateFrom || dateTo

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Review Queue</h1>
        <p className="text-sm text-slate-500 mt-1">
          Review and validate normalized emission records
          {batchFilter && (
            <span className="ml-2 text-primary-400">
              — Filtered by batch
              <button
                onClick={() => navigate('/review')}
                className="ml-1 underline hover:text-primary-300"
              >
                clear
              </button>
            </span>
          )}
        </p>
      </div>

      {/* Filter bar */}
      <div className="glass-card p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Source Type</label>
            <select
              value={sourceType}
              onChange={(e) => { setSourceType(e.target.value); setPage(1) }}
              className="select-dark text-sm py-2.5"
            >
              {sourceTypes.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Severity</label>
            <select
              value={severity}
              onChange={(e) => { setSeverity(e.target.value); setPage(1) }}
              className="select-dark text-sm py-2.5"
            >
              {severityLevels.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">From Date</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => { setDateFrom(e.target.value); setPage(1) }}
              className="input-dark text-sm py-2.5"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">To Date</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => { setDateTo(e.target.value); setPage(1) }}
              className="input-dark text-sm py-2.5"
            />
          </div>

          <div>
            {hasActiveFilters && (
              <button onClick={clearFilters} className="btn-ghost text-sm w-full py-2.5">
                Clear Filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Records table */}
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
            <p className="text-lg font-medium">Failed to load review queue</p>
            <p className="text-sm text-slate-500 mt-1">Please try again.</p>
          </div>
        ) : records.length === 0 ? (
          <div className="text-center py-20 text-slate-500">
            <svg className="w-12 h-12 mx-auto mb-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
            </svg>
            <p className="text-lg font-medium">No records pending review</p>
            <p className="text-sm mt-1">All caught up! Check back later.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Source</th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Entity / Facility</th>
                    <th className="text-right px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Quantity</th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Unit</th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Flags</th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/30">
                  {records.map((record: any, idx: number) => {
                    const flags = record.flags || []
                    const errorCount = record.error_count ?? flags.filter((f: any) => f.severity === 'error').length
                    const warningCount = record.warning_count ?? flags.filter((f: any) => f.severity === 'warning').length
                    const infoCount = record.info_count ?? flags.filter((f: any) => f.severity === 'info').length

                    const badge = scopeBadge[record.source_type] || {
                      label: record.source_type || '—',
                      classes: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
                    }

                    return (
                      <tr
                        key={record.id}
                        onClick={() => navigate(`/review/${record.id}`)}
                        className={`cursor-pointer transition-colors duration-150 hover:bg-white/[0.03] ${
                          idx % 2 === 1 ? 'bg-white/[0.01]' : ''
                        }`}
                      >
                        <td className="px-6 py-4">
                          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${badge.classes}`}>
                            {badge.label}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-medium text-slate-200">
                          {record.facility_or_entity || '—'}
                        </td>
                        <td className="px-6 py-4 text-right text-slate-300 tabular-nums font-mono">
                          {record.quantity_normalized != null
                            ? Number(record.quantity_normalized).toLocaleString()
                            : '—'}
                        </td>
                        <td className="px-6 py-4 text-slate-400">
                          {record.unit_normalized || '—'}
                        </td>
                        <td className="px-6 py-4">
                          {(errorCount + warningCount + infoCount) > 0 ? (
                            <div className="flex items-center gap-2 text-xs">
                              {errorCount > 0 && (
                                <span className="flex items-center gap-1 text-red-400">
                                  <SeverityIcon severity="error" size={14} />
                                  {errorCount}
                                </span>
                              )}
                              {warningCount > 0 && (
                                <span className="flex items-center gap-1 text-amber-400">
                                  <SeverityIcon severity="warning" size={14} />
                                  {warningCount}
                                </span>
                              )}
                              {infoCount > 0 && (
                                <span className="flex items-center gap-1 text-blue-400">
                                  <SeverityIcon severity="info" size={14} />
                                  {infoCount}
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-xs text-slate-600">None</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <StatusPill status={record.review_status || 'pending'} />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
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
    </div>
  )
}

export default ReviewQueuePage
