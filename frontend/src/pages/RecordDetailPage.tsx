import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getReviewRecord, approveRecord, rejectRecord } from '../api/endpoints'
import StatusPill from '../components/StatusPill'
import SeverityIcon from '../components/SeverityIcon'
import Modal from '../components/Modal'

const REJECTION_REASONS = [
  'Data quality issue',
  'Duplicate entry',
  'Incorrect source',
  'Out of scope',
  'Other',
]

const RecordDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [showApproveModal, setShowApproveModal] = useState(false)
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [approveNotes, setApproveNotes] = useState('')
  const [rejectNotes, setRejectNotes] = useState('')
  const [rejectionReason, setRejectionReason] = useState(REJECTION_REASONS[0])

  const { data, isLoading, isError } = useQuery({
    queryKey: ['reviewRecord', id],
    queryFn: () => getReviewRecord(id!),
    enabled: !!id,
  })

  const approveMutation = useMutation({
    mutationFn: () => approveRecord(id!, { notes: approveNotes || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviewRecord', id] })
      queryClient.invalidateQueries({ queryKey: ['reviewQueue'] })
      setShowApproveModal(false)
    },
  })

  const rejectMutation = useMutation({
    mutationFn: () =>
      rejectRecord(id!, {
        rejection_reason: rejectionReason,
        notes: rejectNotes || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviewRecord', id] })
      queryClient.invalidateQueries({ queryKey: ['reviewQueue'] })
      setShowRejectModal(false)
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <svg className="animate-spin w-8 h-8 text-primary-400" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    )
  }

  if (isError || !data?.data) {
    return (
      <div className="text-center py-32">
        <p className="text-lg font-medium text-red-400">Failed to load record</p>
        <button onClick={() => navigate('/review')} className="btn-ghost mt-4">
          ← Back to Review Queue
        </button>
      </div>
    )
  }

  const record = data.data
  const rawPayload = record.raw_payload || {}
  // Build normalized data from the flat fields the serializer returns
  const normalizedData: Record<string, any> = {}
  if (record.quantity_normalized != null) normalizedData['Quantity'] = record.quantity_normalized
  if (record.unit_normalized) normalizedData['Unit'] = record.unit_normalized
  if (record.emission_scope) normalizedData['Emission Scope'] = record.emission_scope
  if (record.source_type) normalizedData['Source Type'] = record.source_type
  if (record.facility_or_entity) normalizedData['Facility / Entity'] = record.facility_or_entity
  if (record.period_start) normalizedData['Period Start'] = record.period_start
  if (record.period_end) normalizedData['Period End'] = record.period_end
  const flags = record.flags || []
  const normalizationLog = record.normalization_log || []
  const isLocked = record.is_locked || record.review_status === 'approved'
  const reviewStatus = record.review_status || 'pending'
  const canAct = reviewStatus === 'pending' && !isLocked

  // Detect fields with error flags
  const errorFields = new Set(
    flags
      .filter((f: any) => f.severity === 'error')
      .map((f: any) => f.field_name || f.field || f.affected_field)
      .filter(Boolean)
  )

  return (
    <div className="space-y-6 animate-fade-in pb-24">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/review')}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/[0.06] transition-all"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-100">Record Detail</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              ID: <span className="font-mono text-slate-400">{id}</span>
            </p>
          </div>
        </div>
        <StatusPill status={reviewStatus} />
      </div>

      {/* Lock banner */}
      {isLocked && (
        <div className="glass-card p-4 flex items-center gap-3 border-amber-500/20 bg-amber-500/5 animate-slide-up">
          <span className="text-xl">🔒</span>
          <p className="text-sm font-medium text-amber-300">
            Audit locked — read only
          </p>
        </div>
      )}

      {/* Two-column layout: Raw + Normalized */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Raw Payload */}
        <div className="glass-card overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-700/40">
            <h2 className="text-base font-semibold text-slate-200">Raw Data</h2>
          </div>
          <div className="p-6">
            {Object.keys(rawPayload).length > 0 ? (
              <div className="space-y-1">
                {Object.entries(rawPayload).map(([key, value]) => {
                  const hasError = errorFields.has(key)
                  return (
                    <div
                      key={key}
                      className={`flex items-start gap-3 py-2 px-3 rounded-lg ${
                        hasError ? 'bg-red-500/10 border border-red-500/20' : 'hover:bg-white/[0.02]'
                      }`}
                    >
                      <span className="text-xs font-medium text-slate-500 min-w-[140px] pt-0.5 font-mono">
                        {key}
                      </span>
                      <span className={`text-sm ${hasError ? 'text-red-300' : 'text-slate-300'}`}>
                        {typeof value === 'object' ? JSON.stringify(value) : String(value ?? '—')}
                      </span>
                      {hasError && <SeverityIcon severity="error" size={16} className="flex-shrink-0 mt-0.5" />}
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="text-sm text-slate-600">No raw data available</p>
            )}
          </div>
        </div>

        {/* Right: Normalized Record */}
        <div className="glass-card overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-700/40">
            <h2 className="text-base font-semibold text-slate-200">Normalized Data</h2>
          </div>
          <div className="p-6">
            {Object.keys(normalizedData).length > 0 ? (
              <div className="space-y-1">
                {Object.entries(normalizedData).map(([key, value]) => (
                  <div key={key} className="flex items-start gap-3 py-2 px-3 rounded-lg hover:bg-white/[0.02]">
                    <span className="text-xs font-medium text-slate-500 min-w-[140px] pt-0.5 font-mono">
                      {key}
                    </span>
                    <span className="text-sm text-slate-300">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value ?? '—')}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-600">No normalized data available</p>
            )}

            {/* Normalization log */}
            {normalizationLog.length > 0 && (
              <div className="mt-6 pt-4 border-t border-slate-700/30">
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  Normalization Log
                </h4>
                <div className="space-y-2">
                  {normalizationLog.map((entry: any, idx: number) => (
                    <div key={idx} className="text-xs text-slate-400 bg-surface-900/60 rounded-lg p-2.5">
                      {typeof entry === 'string' ? entry : JSON.stringify(entry)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Validation Flags */}
      <div className="glass-card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700/40">
          <h2 className="text-base font-semibold text-slate-200">
            Validation Flags
            {flags.length > 0 && (
              <span className="ml-2 text-sm text-slate-500 font-normal">({flags.length})</span>
            )}
          </h2>
        </div>
        <div className="p-6">
          {flags.length > 0 ? (
            <div className="space-y-3">
              {flags.map((flag: any, idx: number) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-4 rounded-xl bg-surface-900/40 border border-slate-700/30"
                >
                  <SeverityIcon severity={flag.severity || 'info'} size={20} className="flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono px-2 py-0.5 rounded-md bg-slate-700/50 text-slate-300">
                        {flag.flag_type || flag.type || 'validation'}
                      </span>
                      {(flag.field_name || flag.field) && (
                        <span className="text-xs text-slate-500">
                          Field: <span className="font-mono text-slate-400">{flag.field_name || flag.field}</span>
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-300">{flag.message || flag.description || '—'}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-600">
              <svg className="w-10 h-10 mx-auto mb-3 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm">No validation flags — record looks clean</p>
            </div>
          )}
        </div>
      </div>

      {/* Sticky action bar */}
      {canAct && (
        <div className="fixed bottom-0 left-0 right-0 z-30 bg-surface-950/80 backdrop-blur-xl border-t border-slate-700/40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-end gap-3">
            <button
              onClick={() => setShowRejectModal(true)}
              className="btn-danger flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              Reject
            </button>
            <button
              onClick={() => setShowApproveModal(true)}
              className="bg-gradient-to-r from-emerald-500 to-green-600 text-white font-semibold px-6 py-2.5 rounded-xl hover:from-emerald-400 hover:to-green-500 transition-all duration-300 shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 active:scale-[0.98] flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              Approve
            </button>
          </div>
        </div>
      )}

      {/* Approve Modal */}
      <Modal
        isOpen={showApproveModal}
        onClose={() => setShowApproveModal(false)}
        title="Approve Record"
        footer={
          <>
            <button onClick={() => setShowApproveModal(false)} className="btn-ghost">
              Cancel
            </button>
            <button
              onClick={() => approveMutation.mutate()}
              disabled={approveMutation.isPending}
              className="bg-gradient-to-r from-emerald-500 to-green-600 text-white font-semibold px-6 py-2.5 rounded-xl hover:from-emerald-400 hover:to-green-500 transition-all duration-300 shadow-lg shadow-emerald-500/25 active:scale-[0.98] disabled:opacity-50 flex items-center gap-2"
            >
              {approveMutation.isPending ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Approving...
                </>
              ) : (
                'Confirm Approval'
              )}
            </button>
          </>
        }
      >
        <p className="text-sm text-slate-400 mb-4">
          Are you sure you want to approve this record? This will lock it for audit.
        </p>

        {approveMutation.isError && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {(approveMutation.error as any)?.response?.data?.detail || 'Approval failed. Please try again.'}
          </div>
        )}

        <label className="block text-sm font-medium text-slate-400 mb-1.5">Notes (optional)</label>
        <textarea
          value={approveNotes}
          onChange={(e) => setApproveNotes(e.target.value)}
          rows={3}
          className="input-dark resize-none"
          placeholder="Add any review notes..."
        />
      </Modal>

      {/* Reject Modal */}
      <Modal
        isOpen={showRejectModal}
        onClose={() => setShowRejectModal(false)}
        title="Reject Record"
        footer={
          <>
            <button onClick={() => setShowRejectModal(false)} className="btn-ghost">
              Cancel
            </button>
            <button
              onClick={() => rejectMutation.mutate()}
              disabled={rejectMutation.isPending}
              className="btn-danger flex items-center gap-2 disabled:opacity-50"
            >
              {rejectMutation.isPending ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Rejecting...
                </>
              ) : (
                'Confirm Rejection'
              )}
            </button>
          </>
        }
      >
        {rejectMutation.isError && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {(rejectMutation.error as any)?.response?.data?.detail || 'Rejection failed. Please try again.'}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">Rejection Reason</label>
            <select
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="select-dark"
            >
              {REJECTION_REASONS.map((reason) => (
                <option key={reason} value={reason}>
                  {reason}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">Notes (optional)</label>
            <textarea
              value={rejectNotes}
              onChange={(e) => setRejectNotes(e.target.value)}
              rows={3}
              className="input-dark resize-none"
              placeholder="Explain the rejection..."
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default RecordDetailPage
