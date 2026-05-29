import { api } from './client'

export const approveRow = (id) => api.post(`/api/review/rows/${id}/approve/`, {})
export const rejectRow = (id, note = '') => api.post(`/api/review/rows/${id}/reject/`, { note })
export const flagRow = (id, reason = '') => api.post(`/api/review/rows/${id}/flag/`, { reason })
export const bulkApprove = (batchId) => api.post(`/api/review/batches/${batchId}/approve-all/`, {})
export const getAuditLog = (id) => api.get(`/api/review/rows/${id}/audit-log/`)
export const getGlobalAuditLog = () => api.get('/api/review/audit-log/?tenant_id=1')
