import React, { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import DragDropZone from '../components/DragDropZone'
import BatchCard from '../components/BatchCard'
import { uploadSAP, uploadUtility, triggerTravel, getBatch, getSources } from '../api/endpoints'

interface UploadSectionProps {
  title: string
  description: string
  accentFrom: string
  accentTo: string
  shadowColor: string
  scopeLabel: string
  scopeColor: string
  children: React.ReactNode
}

const UploadSection: React.FC<UploadSectionProps> = ({
  title,
  description,
  accentFrom,
  accentTo,
  shadowColor,
  scopeLabel,
  scopeColor,
  children,
}) => (
  <div className="glass-card overflow-hidden animate-slide-up">
    {/* Accent bar */}
    <div className={`h-1 bg-gradient-to-r ${accentFrom} ${accentTo}`} />
    <div className="p-6">
      <div className="flex items-center gap-3 mb-1">
        <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
        <span
          className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${scopeColor}`}
        >
          {scopeLabel}
        </span>
      </div>
      <p className="text-sm text-slate-500 mb-5">{description}</p>
      {children}
    </div>
  </div>
)

const UploadPage: React.FC = () => {
  // ─── Fetch Data Sources ─────────────────────────────────────────
  const { data: sourcesResponse, isLoading: isLoadingSources } = useQuery({
    queryKey: ['sources'],
    queryFn: getSources,
  })

  const sources = sourcesResponse?.data?.results || []
  const sapSource = sources.find((s: any) => s.source_type === 'sap_procurement')
  const utilitySource = sources.find((s: any) => s.source_type === 'utility_electricity')
  const travelSource = sources.find((s: any) => s.source_type === 'corporate_travel')

  // ─── SAP State ──────────────────────────────────────────────────
  const [sapFile, setSapFile] = useState<File | null>(null)
  const [sapBatchId, setSapBatchId] = useState<string | null>(null)

  const sapUpload = useMutation({
    mutationFn: ({ file, sourceId }: { file: File; sourceId: string }) => uploadSAP(file, sourceId),
    onSuccess: (res) => {
      setSapBatchId(res.data.id || res.data.batch_id)
    },
  })

  const sapBatchQuery = useQuery({
    queryKey: ['batch', sapBatchId],
    queryFn: () => getBatch(sapBatchId!),
    enabled: !!sapBatchId,
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status
      if (status === 'pending' || status === 'processing') return 3000
      return false
    },
  })

  // ─── Utility State ─────────────────────────────────────────────
  const [utilFile, setUtilFile] = useState<File | null>(null)
  const [utilBatchId, setUtilBatchId] = useState<string | null>(null)

  const utilUpload = useMutation({
    mutationFn: ({ file, sourceId }: { file: File; sourceId: string }) => uploadUtility(file, sourceId),
    onSuccess: (res) => {
      setUtilBatchId(res.data.id || res.data.batch_id)
    },
  })

  const utilBatchQuery = useQuery({
    queryKey: ['batch', utilBatchId],
    queryFn: () => getBatch(utilBatchId!),
    enabled: !!utilBatchId,
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status
      if (status === 'pending' || status === 'processing') return 3000
      return false
    },
  })

  // ─── Travel State ──────────────────────────────────────────────
  const [travelBatchId, setTravelBatchId] = useState<string | null>(null)

  const travelTrigger = useMutation({
    mutationFn: (sourceId: string) => triggerTravel(sourceId),
    onSuccess: (res) => {
      setTravelBatchId(res.data.id || res.data.batch_id)
    },
  })

  const travelBatchQuery = useQuery({
    queryKey: ['batch', travelBatchId],
    queryFn: () => getBatch(travelBatchId!),
    enabled: !!travelBatchId,
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status
      if (status === 'pending' || status === 'processing') return 3000
      return false
    },
  })

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="mb-2">
        <h1 className="text-2xl font-bold text-slate-100">Data Ingestion</h1>
        <p className="text-sm text-slate-500 mt-1">Upload emissions data from various sources</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ─── SAP Procurement ─────────────────────────────────── */}
        <UploadSection
          title="SAP Procurement"
          description="Upload procurement data for Scope 1 direct emissions"
          accentFrom="from-red-500"
          accentTo="to-orange-500"
          shadowColor="shadow-red-500/5"
          scopeLabel="Scope 1"
          scopeColor="bg-red-500/15 text-red-400 border border-red-500/30"
        >
          <DragDropZone
            onFileSelect={setSapFile}
            label="Drop SAP procurement CSV here"
            disabled={sapUpload.isPending}
          />

          {sapFile && !sapBatchId && (
            <button
              onClick={() => {
                if (sapSource?.id) {
                  sapUpload.mutate({ file: sapFile, sourceId: sapSource.id })
                }
              }}
              disabled={sapUpload.isPending || !sapSource?.id}
              className="w-full btn-primary mt-4 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {sapUpload.isPending ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Uploading...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                  </svg>
                  Upload SAP Data
                </>
              )}
            </button>
          )}

          {!sapSource && !isLoadingSources && (
            <p className="text-xs text-amber-500/80 mt-2 text-center animate-pulse">
              ⚠️ No active SAP data source found.
            </p>
          )}
 
           {sapUpload.isError && (
             <p className="text-sm text-red-400 mt-3">
               Upload failed: {(sapUpload.error as any)?.response?.data?.detail || (sapUpload.error as any)?.response?.data?.error || 'Unknown error'}
             </p>
           )}
 
           {sapBatchQuery.data?.data && <BatchCard batch={sapBatchQuery.data.data} />}
         </UploadSection>
 
         {/* ─── Utility Electricity ─────────────────────────────── */}
         <UploadSection
           title="Utility Electricity"
           description="Upload utility bills for Scope 2 indirect emissions"
           accentFrom="from-amber-500"
           accentTo="to-yellow-500"
           shadowColor="shadow-amber-500/5"
           scopeLabel="Scope 2"
           scopeColor="bg-amber-500/15 text-amber-400 border border-amber-500/30"
         >
           <DragDropZone
             onFileSelect={setUtilFile}
             label="Drop utility electricity CSV here"
             disabled={utilUpload.isPending}
           />
 
           {utilFile && !utilBatchId && (
             <button
               onClick={() => {
                 if (utilitySource?.id) {
                   utilUpload.mutate({ file: utilFile, sourceId: utilitySource.id })
                 }
               }}
               disabled={utilUpload.isPending || !utilitySource?.id}
               className="w-full btn-primary mt-4 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
             >
               {utilUpload.isPending ? (
                 <>
                   <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                     <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                     <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                   </svg>
                   Uploading...
                 </>
               ) : (
                 <>
                   <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                     <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                   </svg>
                   Upload Utility Data
                 </>
               )}
             </button>
           )}

          {!utilitySource && !isLoadingSources && (
            <p className="text-xs text-amber-500/80 mt-2 text-center animate-pulse">
              ⚠️ No active Utility data source found.
            </p>
          )}
 
           {utilUpload.isError && (
             <p className="text-sm text-red-400 mt-3">
               Upload failed: {(utilUpload.error as any)?.response?.data?.detail || (utilUpload.error as any)?.response?.data?.error || 'Unknown error'}
             </p>
           )}
 
           {utilBatchQuery.data?.data && <BatchCard batch={utilBatchQuery.data.data} />}
         </UploadSection>
 
         {/* ─── Corporate Travel ────────────────────────────────── */}
         <UploadSection
           title="Corporate Travel"
           description="Pull travel data from API for Scope 3 emissions"
           accentFrom="from-teal-500"
           accentTo="to-cyan-500"
           shadowColor="shadow-teal-500/5"
           scopeLabel="Scope 3"
           scopeColor="bg-teal-500/15 text-teal-400 border border-teal-500/30"
         >
           <div className="flex flex-col items-center gap-4 py-4">
             <div className="w-16 h-16 rounded-2xl bg-teal-500/10 flex items-center justify-center">
               <svg className="w-8 h-8 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                 <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
               </svg>
             </div>
 
             <p className="text-sm text-slate-400 text-center">
               No file needed — data is pulled directly from the corporate travel API.
             </p>
 
             <button
               onClick={() => {
                 if (travelSource?.id) {
                   travelTrigger.mutate(travelSource.id)
                 }
               }}
               disabled={travelTrigger.isPending || !travelSource?.id}
               className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
             >
               {travelTrigger.isPending ? (
                 <>
                   <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                     <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                     <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                   </svg>
                   Pulling data...
                 </>
               ) : (
                 <>
                   <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                     <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                   </svg>
                   Pull from Travel API
                 </>
               )}
             </button>
           </div>

          {!travelSource && !isLoadingSources && (
            <p className="text-xs text-amber-500/80 mt-2 text-center animate-pulse">
              ⚠️ No active Corporate Travel data source found.
            </p>
          )}
 
           {travelTrigger.isError && (
             <p className="text-sm text-red-400 mt-3">
               Failed: {(travelTrigger.error as any)?.response?.data?.detail || (travelTrigger.error as any)?.response?.data?.error || 'Unknown error'}
             </p>
          )}

          {travelBatchQuery.data?.data && <BatchCard batch={travelBatchQuery.data.data} />}
        </UploadSection>
      </div>
    </div>
  )
}

export default UploadPage
