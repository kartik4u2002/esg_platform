import api from './client'

// ─── Auth ───────────────────────────────────────────────────────────
export const login = (email: string, password: string) =>
  api.post('/api/v1/auth/token/', { username: email, password })

export const refreshToken = (refresh: string) =>
  api.post('/api/v1/auth/token/refresh/', { refresh })

// ─── Ingestion / Sources ────────────────────────────────────────────
export const getSources = () =>
  api.get('/api/v1/ingestion/sources/')

export const createSource = (data: Record<string, unknown>) =>
  api.post('/api/v1/ingestion/sources/', data)

// ─── Ingestion / Batches ────────────────────────────────────────────
export const getBatches = (params?: Record<string, unknown>) =>
  api.get('/api/v1/ingestion/batches/', { params })

export const getBatch = (id: string) =>
  api.get(`/api/v1/ingestion/batches/${id}/`)

// ─── Ingestion / Upload ─────────────────────────────────────────────
export const uploadSAP = (file: File, sourceId: string) => {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('source_id', sourceId)
  return api.post('/api/v1/ingestion/upload/sap/', fd)
}

export const uploadUtility = (file: File, sourceId: string) => {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('source_id', sourceId)
  return api.post('/api/v1/ingestion/upload/utility/', fd)
}

export const triggerTravel = (sourceId: string) =>
  api.post('/api/v1/ingestion/travel/trigger/', { source_id: sourceId })

// ─── Review ─────────────────────────────────────────────────────────
export const getReviewQueue = (params?: Record<string, unknown>) =>
  api.get('/api/v1/review/queue/', { params })

export const getReviewRecord = (id: string) =>
  api.get(`/api/v1/review/records/${id}/`)

export const approveRecord = (id: string, data: { notes?: string }) =>
  api.post(`/api/v1/review/records/${id}/approve/`, data)

export const rejectRecord = (id: string, data: { notes?: string; rejection_reason: string }) =>
  api.post(`/api/v1/review/records/${id}/reject/`, data)

// ─── Audit ──────────────────────────────────────────────────────────
export const getAuditRecords = (params?: Record<string, unknown>) =>
  api.get('/api/v1/audit/records/', { params })

export const getAuditTrail = (id: string) =>
  api.get(`/api/v1/audit/records/${id}/trail/`)

export const exportAuditCSV = () =>
  api.get('/api/v1/audit/export/', { params: { format: 'csv' }, responseType: 'blob' })
