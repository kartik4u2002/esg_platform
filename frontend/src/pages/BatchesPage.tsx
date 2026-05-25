import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getBatches } from '../api/endpoints'
import StatusPill from '../components/StatusPill'

const BatchesPage: React.FC = () => {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const pageSize = 15

  const { data, isLoading, isError } = useQuery({
    queryKey: ['batches', page],
    queryFn: () => getBatches({ page, page_size: pageSize }),
  })

  const batches = data?.data?.results || data?.data || []
  const totalCount = data?.data?.count || batches.length
  const totalPages = Math.ceil(totalCount / pageSize) || 1

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

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Ingestion Batches</h1>
        <p className="text-sm text-slate-500 mt-1">Track the status of all data ingestion batches</p>
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
            <p className="text-lg font-medium">Failed to load batches</p>
            <p className="text-sm text-slate-500 mt-1">Please check your connection and try again.</p>
          </div>
        ) : batches.length === 0 ? (
          <div className="text-center py-20 text-slate-500">
            <svg className="w-12 h-12 mx-auto mb-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
            </svg>
            <p className="text-lg font-medium">No batches yet</p>
            <p className="text-sm mt-1">Upload data from the Upload page to get started.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Source</th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">File Name</th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                    <th className="text-right px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Rows</th>
                    <th className="text-right px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Processed</th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Ingested By</th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/30">
                  {batches.map((batch: any, idx: number) => (
                    <tr
                      key={batch.id}
                      onClick={() => navigate(`/review?batch=${batch.id}`)}
                      className={`cursor-pointer transition-colors duration-150 hover:bg-white/[0.03] ${
                        idx % 2 === 1 ? 'bg-white/[0.01]' : ''
                      }`}
                    >
                      <td className="px-6 py-4 font-medium text-slate-200">
                        {batch.source_name || batch.source?.name || '—'}
                      </td>
                      <td className="px-6 py-4 text-slate-400 truncate max-w-[200px]">
                        {batch.file_name || '—'}
                      </td>
                      <td className="px-6 py-4">
                        <StatusPill status={batch.status} />
                      </td>
                      <td className="px-6 py-4 text-right text-slate-300 tabular-nums">
                        {batch.total_rows ?? '—'}
                      </td>
                      <td className="px-6 py-4 text-right text-slate-300 tabular-nums">
                        {batch.processed_rows ?? '—'}
                      </td>
                      <td className="px-6 py-4 text-slate-400">
                        {batch.ingested_by_name || '—'}
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-xs whitespace-nowrap">
                        {formatDate(batch.ingested_at || batch.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-slate-700/40">
                <p className="text-xs text-slate-500">
                  Page {page} of {totalPages} · {totalCount} total batches
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

export default BatchesPage
